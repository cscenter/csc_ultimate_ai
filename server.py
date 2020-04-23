import asyncio
import dataclasses
import json
from dataclasses import dataclass
from typing import Optional, cast, Dict

import dataclass_factory
import zmq.asyncio
from zmq.asyncio import Context
import traceback

from base.protocol import MessageOutType, MessageOut, Hello, Pong, OfferResponse, DealResponse, ReadyMsg, MessageInType, \
    MessageIn
import logging
import sys

from base.util import init_stdout_logging


# def decode_msg(msg_data) -> Optional[MessageOut]:
#     try:
#         # msg_data = json.loads(raw_msg)
#         msg_type = msg_data['msg_type']
#         msg_payload = msg_data['payload']
#         if msg_type == MessageOutType.HELLO:
#             return MessageOut(msg_type, Hello(**msg_payload))
#         elif msg_type == MessageOutType.PONG:
#             return MessageOut(msg_type, Pong(**msg_payload))
#         elif msg_type == MessageOutType.OFFER_RESPONSE:
#             return MessageOut(msg_type, OfferResponse(**msg_payload))
#         elif msg_type == MessageOutType.DEAL_RESPONSE:
#             return MessageOut(msg_type, DealResponse(**msg_payload))
#     except ValueError as e:
#         logging.exception("Decoding error")
#     return None


@dataclass
class AgentState:
    name: str
    agent_id: int
    current_round: int = 0
    total_rounds: int = 0
    wins: int = 0
    total_gain: int = 0


class Server:

    def __init__(self):
        self.await_agents = 2
        self.url = '127.0.0.1'
        self.port = '5555'
        self.url = "tcp://{}:{}".format(self.url, self.port)
        self.ctx = Context.instance()

    def start(self):
        asyncio.get_event_loop().run_until_complete(asyncio.wait([
            self.server_handler()
        ]))

    async def server_handler(self):
        mq_socket = None
        try:
            mq_socket = await self.init_mq_router_socket()
            agents_state = await self.wait_all_clients(mq_socket)
            await self.send_ready_for_all(mq_socket, agents_state)
        except Exception as e:
            logging.exception("Server error.")
        finally:
            if mq_socket:
                logging.info("Close socket.")
                mq_socket.close()

    async def init_mq_router_socket(self) -> zmq.Socket:
        mq_socket = self.ctx.socket(zmq.ROUTER)
        mq_socket.bind(self.url[:-1] + "{}".format(int(self.url[-1]) + 1))
        logging.info("MQ router socket initialized")
        return mq_socket

    async def wait_all_clients(self, mq_socket: zmq.Socket) -> Dict[str, AgentState]:
        agents_state = {}
        counter = 0
        logging.info("Wait clients ...")
        while len(agents_state) < self.await_agents:
            connection_uid = await mq_socket.recv()
            connection_uid = connection_uid.decode('utf-8')
            raw_msg = await mq_socket.recv_json()
            if raw_msg.get('msg_type', None) == MessageOutType.HELLO:
                counter += 1
                msg_payload = raw_msg['payload']
                hello_msg = Hello(**msg_payload)
                agents_state[connection_uid] = AgentState(name=hello_msg.my_name, agent_id=counter)
                logging.info(f"New client connected. agent_id:{counter} name:'{hello_msg.my_name}'"
                             f" uid:{connection_uid}")

        logging.info(f"All {len(agents_state)} connected")
        return agents_state

    async def send_ready_for_all(self, mq_socket: zmq.Socket, agents_state: Dict[str, AgentState]):
        for connection_uid, state in agents_state.items():
            await mq_socket.send_string(connection_uid, zmq.SNDMORE)
            msg = MessageIn(MessageInType.READY, ReadyMsg(state.agent_id))
            await mq_socket.send_json(dataclasses.asdict(msg))


if __name__ == '__main__':
    init_stdout_logging()
    server = Server()
    server.start()
