import asyncio
import dataclasses
import uuid
from typing import Optional

import dataclass_factory
import zmq.asyncio
from zmq.asyncio import Context
import traceback
import logging

from base.protocol import Hello, MessageOut, MessageOutType, MessageInType, MessageIn, ReadyMsg
from base.util import init_stdout_logging


class Client:

    def __init__(self):
        self.url = '127.0.0.1'
        self.port = '5555'
        self.url = "tcp://{}:{}".format(self.url, self.port)
        self.ctx = Context.instance()
        self.connection_uid = str(uuid.uuid4())

    # def decode_msg(self,msg_data) -> Optional[MessageIn]:
    #     try:
    #         # msg_data = json.loads(raw_msg)
    #         msg_type = msg_data['msg_type']
    #         msg_payload = msg_data['payload']
    #         if msg_type == MessageInType.READY:
    #             return MessageIn(msg_type, ReadyMsg(**msg_payload))
    #         elif msg_type == MessageOutType.:
    #             return MessageIn(msg_type, Pong(**msg_payload))
    #         elif msg_type == MessageOutType.OFFER_RESPONSE:
    #             return MessageIn(msg_type, OfferResponse(**msg_payload))
    #         elif msg_type == MessageOutType.DEAL_RESPONSE:
    #             return MessageIn(msg_type, DealResponse(**msg_payload))
    #     except ValueError as e:
    #         logging.exception("Decoding error")
    #     return None

    def start(self):
        asyncio.get_event_loop().run_until_complete(asyncio.wait([
            self.client_handler()
        ]))

    async def client_handler(self):
        mq_socket = None
        try:
            mq_socket = await self.init_mq_dealer_socket()
            # give time to router to initialize; wait time >.2 sec
            await asyncio.sleep(.3)
            await self.send_hello(mq_socket, "Vasia")
            ready_msg = await self.wait_ready_msg(mq_socket)
            print(ready_msg)

        except Exception as e:
            logging.exception("Client error.")
        finally:
            if mq_socket:
                logging.info("Close socket.")
                mq_socket.close()

    async def init_mq_dealer_socket(self):
        mq_socket = self.ctx.socket(zmq.DEALER)
        mq_socket.setsockopt(zmq.IDENTITY, bytes(self.connection_uid, 'utf-8'))
        mq_socket.connect(self.url[:-1] + "{}".format(int(self.url[-1]) + 1))
        logging.info(f"MQ dealer socket initialized. Connection uid:{self.connection_uid}")
        return mq_socket

    async def send_hello(self, mq_socket, name):
        logging.info("Send 'hello' to server")
        msg = MessageOut(MessageOutType.HELLO, Hello(name))
        await mq_socket.send_json(dataclasses.asdict(msg))

    async def wait_ready_msg(self, deal):
        logging.info("Wait 'ready' from server ...")
        while True:
            await asyncio.sleep(.1)
            response = await deal.recv_json()
            if response.get('msg_type', None) == MessageInType.READY:
                msg_payload = response['payload']
                return ReadyMsg(**msg_payload)


if __name__ == '__main__':
    init_stdout_logging()
    client = Client()
    client.start()
