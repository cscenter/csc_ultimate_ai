import asyncio
import dataclasses
import json
from dataclasses import dataclass
from typing import Optional, cast

import dataclass_factory
import zmq.asyncio
from zmq.asyncio import Context
import traceback

from base.protocol import MessageOutType, MessageOut, Hello, Pong, OfferResponse, DealResponse, ReadyMsg, MessageInType, \
    MessageIn
import logging
import sys

from base.util import init_stdout_logging

init_stdout_logging()

url = '127.0.0.1'
port = '5555'
url = "tcp://{}:{}".format(url, port)
# pub/sub and dealer/router
ctx = Context.instance()
factory = dataclass_factory.Factory()

AWAIT_AGENTS = 2


def decode_msg(msg_data) -> Optional[MessageOut]:
    try:
        # msg_data = json.loads(raw_msg)
        msg_type = msg_data['msg_type']
        msg_payload = msg_data['payload']
        if msg_type == MessageOutType.HELLO:
            return MessageOut(msg_type, Hello(**msg_payload))
        elif msg_type == MessageOutType.PONG:
            return MessageOut(msg_type, Pong(**msg_payload))
        elif msg_type == MessageOutType.OFFER_RESPONSE:
            return MessageOut(msg_type, OfferResponse(**msg_payload))
        elif msg_type == MessageOutType.DEAL_RESPONSE:
            return MessageOut(msg_type, DealResponse(**msg_payload))
    except ValueError as e:
        logging.exception("Decoding error")
    return None


@dataclass
class AgentState:
    name: str
    agent_id: int
    current_round: int = 0
    total_rounds: int = 0
    wins: int = 0
    total_gain: int = 0


async def server_handler():
    # setup router
    rout = ctx.socket(zmq.ROUTER)
    rout.bind(url[:-1] + "{}".format(int(url[-1]) + 1))
    # rout.setsockopt(zmq.SUBSCRIBE, b'')
    logging.info("Server router initialized. Wait agents ...")
    try:
        agents_state = {}
        # Wait all agents
        counter = 0
        while len(agents_state) < AWAIT_AGENTS:
            connection_uid = await rout.recv()
            raw_msg = await rout.recv_json()
            # [connection_uid, raw_msg] = await rout.recv_multipart()
            msg = decode_msg(raw_msg)
            if msg and msg.msg_type == MessageOutType.HELLO and connection_uid not in agents_state:
                counter += 1
                payload = cast(Hello, msg.payload)
                agents_state[connection_uid] = AgentState(name=payload.my_name, agent_id=counter)
                logging.info(f"New client connected name:'{payload.my_name}' uid:{connection_uid}")

        logging.info(f"All {len(agents_state)} connected")
        for connection_uid, state in agents_state.items():
            await rout.send(connection_uid, zmq.SNDMORE)
            msg = MessageIn(MessageInType.READY, ReadyMsg(state.agent_id))
            await rout.send_json(dataclasses.asdict(msg))


    except Exception as e:
        print("Error with sub world")
        # print(e)
        logging.error(traceback.format_exc())
        print()

    finally:
        # TODO disconnect dealer/router
        pass


asyncio.get_event_loop().run_until_complete(asyncio.wait([
    server_handler()]))
