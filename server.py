import asyncio
import dataclasses
import datetime
import json
import logging
import os
import random
import time
from dataclasses import dataclass
from typing import Optional, Dict, List, Tuple

import numpy as np
import zmq.asyncio
from zmq.asyncio import Context

from base.protocol import MessageOutType, Hello, OfferResponse, DealResponse, ReadyMsg, MessageInType, \
    MessageIn, OfferRequest, DealRequest, RoundResult
from base.util import init_stdout_logging, init_file_logging


@dataclass
class AgentState:
    uid: str
    name: str
    current_round: int = 0
    total_rounds: int = 0
    wins: int = 0
    last_action_time: float = 0
    timeout_disconnected: bool = False
    gain_history: List[int] = dataclasses.field(default_factory=list)


@dataclass
class Round:
    round_id: int
    total_amount: int
    proposer: AgentState
    responder: AgentState
    proposer_offer: int = 0
    responder_accepted: bool = False
    proposer_disconnected: bool = False
    responder_disconnected: bool = False

    def is_failed(self) -> bool:
        return self.proposer_disconnected or self.responder_disconnected


class Server:

    def __init__(self):
        self.min_round_perc = int((os.getenv('MIN_ROUND_PERC', 1)))
        self.total_offer = int((os.getenv('TOTAL_OFFER', 100)))
        self.agent_round_limit = int(os.getenv('TOTAL_ROUNDS', 100))
        self.await_agents = int((os.getenv('CLIENTS_AMOUNT', 2)))
        self.agent_timeout = int(os.getenv('RESPONSE_TIMEOUT', 2))
        self.url = os.getenv('SERVER_URL', '127.0.0.1')
        self.port = os.getenv('SERVER_PORT', '4181')
        self.log_progress_delay = os.getenv('LOG_PROGRESS_DELAY', 1)
        self.url = "tcp://{}:{}".format(self.url, self.port)
        self.ctx = Context.instance()
        self.mq_socket: Optional[zmq.Socket] = None
        self.agents_state: Dict[str, AgentState] = {}
        self.last_progress_log = None

    def start(self):
        asyncio.get_event_loop().run_until_complete(asyncio.wait([
            self.server_handler()
        ]))

    async def server_handler(self):
        try:
            await self.init_mq_router_socket()
            new_agents_state = await self.wait_all_clients()
            self.set_agents_state(new_agents_state)
            await self.send_ready_for_all()
            await asyncio.sleep(.3)
            round_counter: int = 0
            while not self.is_stop_criteria():
                self.print_round_progress(round_counter)
                round_counter, rounds = self.generate_rounds(round_counter)
                await self.send_offer_questions(rounds)
                await self.wait_all_offer_answers(rounds)
                await self.send_deal_questions(rounds)
                await self.wait_deal_answers(rounds)
                await self.send_result_for_all(rounds)

            await self.send_complete_for_all()
            self.show_stat()
        except Exception:
            logging.exception("Server error.")
        finally:
            if self.mq_socket:
                logging.info("Close socket.")
                self.mq_socket.close()

    async def init_mq_router_socket(self):
        mq_socket = self.ctx.socket(zmq.ROUTER)
        mq_socket.bind(self.url[:-1] + "{}".format(int(self.url[-1]) + 1))
        logging.info("MQ router socket initialized")
        self.mq_socket = mq_socket

    async def wait_all_clients(self) -> Dict[str, AgentState]:
        agents_state = {}
        counter = 0
        logging.info(f"Wait ({self.await_agents}) clients ...")
        while len(agents_state) < self.await_agents:
            connection_uid = await self.mq_socket.recv_string()
            raw_msg = await self.mq_socket.recv_json()
            logging.debug("Received from %s msg: %s", connection_uid, raw_msg)
            if raw_msg.get('msg_type', None) == MessageOutType.HELLO:
                counter += 1
                msg_payload = raw_msg['payload']
                hello_msg = Hello(**msg_payload)
                error = hello_msg.find_error()
                if error:
                    raise Exception(f"Wrong 'hello' from {connection_uid}. Error: {error}")
                else:
                    agents_state[connection_uid] = AgentState(
                        uid=connection_uid, name=hello_msg.my_name
                    )
                    logging.info(f"New client connected. name:'{hello_msg.my_name}'"
                                 f" uid:{connection_uid}")

        logging.info(f"All {len(agents_state)} connected")
        return agents_state

    def set_agents_state(self, agents_state: Dict[str, AgentState]):
        self.agents_state = agents_state

    async def send_ready_for_all(self):
        for connection_uid, state in self.agents_state.items():
            await self.mq_socket.send_string(connection_uid, zmq.SNDMORE)
            msg = MessageIn(MessageInType.READY, ReadyMsg(state.uid))
            await self.mq_socket.send_json(dataclasses.asdict(msg))

    def is_stop_criteria(self) -> bool:
        return any([
            # max rounds criteria
            all(x.total_rounds >= self.agent_round_limit
                for x in self.agents_state.values() if not x.timeout_disconnected
                ),
            # min clients criteria
            sum(1 for x in self.agents_state.values() if not x.timeout_disconnected) < 2
        ])

    def generate_rounds(self, round_counter: int) -> Tuple[int, List[Round]]:
        ready_agents = [x for x in self.agents_state.values() if not x.timeout_disconnected]
        random.shuffle(ready_agents)
        rnd_agent_pairs = [(ready_agents[i * 2], ready_agents[i * 2 + 1])
                           for i in range(len(ready_agents) // 2)]
        result = []
        for first, second in rnd_agent_pairs:
            round_counter += 1
            result.append(Round(
                round_id=round_counter,
                total_amount=self.total_offer,
                proposer=first,
                responder=second
            ))
        logging.debug("Generated %s rounds. "
                      "Pairs: %s", len(result), [(r.proposer.uid, r.responder.uid) for r in result])
        return round_counter, result

    async def send_offer_questions(self, rounds: List[Round]):
        for r in rounds:
            connection_uid = r.proposer.uid
            logging.debug("Send offer request to %s", connection_uid)
            await self.mq_socket.send_string(connection_uid, zmq.SNDMORE)
            msg = MessageIn(MessageInType.OFFER_REQUEST, OfferRequest(
                round_id=r.round_id,
                target_agent_uid=r.responder.uid,
                total_amount=r.total_amount
            ))
            await self.mq_socket.send_json(dataclasses.asdict(msg))
            agent = self.agents_state[connection_uid]
            agent.last_action_time = time.time()
            agent.current_round = r.round_id

    async def wait_all_offer_answers(self, rounds: List[Round]):
        wait_for_rounds: Dict[str, Round] = {r.proposer.uid: r for r in rounds if not r.is_failed()}

        async def inner_handler():
            while len(wait_for_rounds) > 0:
                connection_uid = await self.mq_socket.recv_string()
                raw_msg = await self.mq_socket.recv_json()
                logging.debug("Received from %s msg: %s", connection_uid, raw_msg)
                if connection_uid in wait_for_rounds and raw_msg.get('msg_type', None) == MessageOutType.OFFER_RESPONSE:
                    r = wait_for_rounds[connection_uid]
                    offer_response = OfferResponse(**raw_msg['payload'])
                    if offer_response.offer > r.total_amount:
                        error = f"Offer {offer_response.offer} is to large"
                    else:
                        error = offer_response.find_error()
                    if error:
                        logging.error(f"Wrong offer response from {connection_uid} skip it. Error: {error}")
                    else:
                        r.proposer_offer = offer_response.offer
                        r.proposer.last_action_time = time.time()
                        del wait_for_rounds[connection_uid]

        try:
            await asyncio.wait_for(inner_handler(), timeout=self.agent_timeout)
        except asyncio.TimeoutError:
            for uid, r in wait_for_rounds.items():
                logging.debug("Wait offer response timeout from %s", uid)
                r.proposer_disconnected = True
                self.agents_state[uid].timeout_disconnected = True
                # notify responder
                result = RoundResult(
                    round_id=r.round_id,
                    win=False,
                    agent_gain={r.responder.uid: 0, r.proposer.uid: 0},
                    disconnection_failure=True
                )
                await self.save_stat_and_notify(r.responder.uid, result)

    async def send_deal_questions(self, rounds: List[Round]):
        for r in rounds:
            if not r.is_failed():
                connection_uid = r.responder.uid
                await self.mq_socket.send_string(connection_uid, zmq.SNDMORE)
                msg = MessageIn(MessageInType.DEAL_REQUEST, DealRequest(
                    round_id=r.round_id,
                    from_agent_uid=r.proposer.uid,
                    total_amount=r.total_amount,
                    offer=r.proposer_offer
                ))
                await self.mq_socket.send_json(dataclasses.asdict(msg))
                agent = self.agents_state[connection_uid]
                agent.last_action_time = time.time()
                agent.current_round = r.round_id

    async def wait_deal_answers(self, rounds: List[Round]):
        wait_for_rounds: Dict[str, Round] = {r.responder.uid: r for r in rounds if not r.is_failed()}

        async def inner_handler():
            while len(wait_for_rounds) > 0:
                connection_uid = await self.mq_socket.recv_string()
                raw_msg = await self.mq_socket.recv_json()
                logging.debug("Received from %s msg: %s", connection_uid, raw_msg)
                if connection_uid in wait_for_rounds and raw_msg.get('msg_type', None) == MessageOutType.DEAL_RESPONSE:
                    r = wait_for_rounds[connection_uid]
                    deal_response = DealResponse(**raw_msg['payload'])
                    error = deal_response.find_error()
                    if error:
                        logging.error(f"Wrong deal response from {connection_uid} skip it. Error: {error}")
                    else:
                        r.responder_accepted = deal_response.accepted
                        r.responder.last_action_time = time.time()
                        del wait_for_rounds[connection_uid]

        try:
            await asyncio.wait_for(inner_handler(), timeout=self.agent_timeout)
        except asyncio.TimeoutError:
            for uid, r in wait_for_rounds.items():
                logging.debug("Wait deal response timeout from %s", uid)
                r.responder_disconnected = True
                self.agents_state[uid].timeout_disconnected = True
                # notify proposer
                result = RoundResult(
                    round_id=r.round_id,
                    win=False,
                    agent_gain={r.responder.uid: 0, r.proposer.uid: 0},
                    disconnection_failure=True
                )
                await self.save_stat_and_notify(r.proposer.uid, result)

    async def send_result_for_all(self, rounds: List[Round]):
        for r in rounds:
            if not r.is_failed():
                # agent offer aception rules
                if r.responder_accepted:
                    proposer_gain = (r.total_amount - r.proposer_offer)
                    responder_gain = r.proposer_offer
                else:
                    proposer_gain = 0
                    responder_gain = 0
                result = RoundResult(
                    round_id=r.round_id,
                    win=r.responder_accepted,
                    agent_gain={
                        r.proposer.uid: proposer_gain,
                        r.responder.uid: responder_gain},
                    disconnection_failure=False
                )
                await self.save_stat_and_notify(r.proposer.uid, result)
                await self.save_stat_and_notify(r.responder.uid, result)

    async def send_complete_for_all(self):
        for agent in self.agents_state.values():
            uid = agent.uid
            msg = MessageIn(MessageInType.COMPLETE, None)
            logging.debug("Send 'complete' to %s. Msg: %s", uid, msg)
            await self.mq_socket.send_string(uid, zmq.SNDMORE)
            await self.mq_socket.send_json(dataclasses.asdict(msg))

    async def save_stat_and_notify(self, uid: str, result: RoundResult):
        agent = self.agents_state[uid]
        if not result.disconnection_failure:
            agent.total_rounds += 1
            if result.win:
                agent.wins += 1
            gain = result.agent_gain[uid]
            agent.gain_history.append(gain)

        msg = MessageIn(MessageInType.ROUND_RESULT, result)
        logging.debug("Result notify to %s. Result: %s", uid, result)
        await self.mq_socket.send_string(uid, zmq.SNDMORE)
        await self.mq_socket.send_json(dataclasses.asdict(msg))

    def show_stat(self):
        result_list = []
        disqualification = []
        for agent in self.agents_state.values():
            gains = np.array(agent.gain_history)
            if len(gains) > self.agent_round_limit * self.min_round_perc / 100:
                C = 18
                m = self.total_offer / 2
                score = (C*m + gains.sum())/(C+len(gains))
                result_list.append((score, gains, agent))
            else:
                disqualification.append((gains, agent))
        result_list.sort(key=lambda x: x[0], reverse=True)
        result_dict = {
            'headers': ['Place', 'Agent', 'Score', 'Mean gain (±std)', 'Rounds', 'Status'],
            'data': [],
            'competition_time': datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
        }
        for i, (score, gains, agent) in enumerate(result_list):
            row = {
                'Place': f"{i + 1}",
                'Agent': agent.name,
                'Score': f"{score:0.4f}",
                'Mean gain (±std)': f"{gains.mean():0.4f}±{gains.std() / np.sqrt(len(gains)):0.4f}",
                'Rounds': f"{len(gains)}",
                'Status': 'Ok'
            }
            result_dict['data'].append(row)

        for i, (gains, agent) in enumerate(disqualification):
            row = {
                'Place': '_',
                'Agent': agent.name,
                'Score': '_',
                'Mean gain (±std)': '_',
                'Rounds': f"{len(gains)}",
                'Status': 'Timeout disqualification'
            }
            result_dict['data'].append(row)

        logging.info(f"ROUND_JSON_DATA:{json.dumps(result_dict)}")
        # Inplace table
        headers = '\t'.join(result_dict['headers'])
        report_str = f"\nCompetition results:\n{headers}"
        for row in result_dict['data']:
            row_str = '\t'.join([row[header] for header in result_dict['headers']])
            report_str += f"\n{row_str}"
        logging.info(report_str)

    def print_round_progress(self, round_counter):
        time_now = time.time()
        if self.last_progress_log is None:
            self.last_progress_log = time_now
            logging.info("Game started ...")
        else:
            if time_now > self.last_progress_log + self.log_progress_delay:
                logging.info(f"Round: {round_counter} limit: {(self.agent_round_limit * self.await_agents) // 2}")
                self.last_progress_log = time_now


if __name__ == '__main__':
    init_stdout_logging()
    init_file_logging('logs/server.log')
    server = Server()
    server.start()
