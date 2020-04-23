import asyncio
import dataclasses
import logging
import uuid

import zmq.asyncio
from zmq.asyncio import Context

from agent.base import BaseAgent
from base.protocol import Hello, MessageOut, MessageOutType, MessageInType, ReadyMsg, OfferRequest, \
    DealRequest, RoundResult, OfferResponse, DealResponse
from base.util import init_stdout_logging


class Client:

    def __init__(self):
        self.class_path = 'agent.chaotic.ChaoticAgent'
        self.url = '127.0.0.1'
        self.port = '5555'
        self.url = "tcp://{}:{}".format(self.url, self.port)
        self.ctx = Context.instance()
        self.connection_uid = str(uuid.uuid4())

    def start(self):
        asyncio.get_event_loop().run_until_complete(asyncio.wait([
            self.client_handler()
        ]))

    async def client_handler(self):
        mq_socket = None
        try:
            # initialization part
            agent = self.init_ai_agent()
            mq_socket = await self.init_mq_dealer_socket()
            # give time to router to initialize; wait time >.2 sec
            await asyncio.sleep(.3)
            await self.send_hello(mq_socket, agent.get_my_name())
            ready_msg = await self.wait_ready_msg(mq_socket)
            agent.agent_id = ready_msg.your_agent_id
            # game loop part
            while True:
                await self.handle_game_round(mq_socket, agent)

        except Exception as e:
            logging.exception("Client error.")
        finally:
            if mq_socket:
                logging.info("Close socket.")
                mq_socket.close()

    def init_ai_agent(self) -> BaseAgent:
        split_result = self.class_path.rsplit('.', 1)
        class_name = split_result[1]
        module_path = split_result[0]
        mod = __import__(module_path, fromlist=[class_name])
        klass = getattr(mod, class_name)
        instance = klass()
        return instance

    async def init_mq_dealer_socket(self) -> zmq.Socket:
        mq_socket = self.ctx.socket(zmq.DEALER)
        mq_socket.setsockopt(zmq.IDENTITY, bytes(self.connection_uid, 'utf-8'))
        mq_socket.connect(self.url[:-1] + "{}".format(int(self.url[-1]) + 1))
        logging.info(f"MQ dealer socket initialized. Connection uid:{self.connection_uid}")
        return mq_socket

    async def send_hello(self, mq_socket: zmq.Socket, name: str):
        logging.info("Send 'hello' to server")
        msg = MessageOut(MessageOutType.HELLO, Hello(name))
        await mq_socket.send_json(dataclasses.asdict(msg))

    async def wait_ready_msg(self, mq_socket: zmq.Socket) -> ReadyMsg:
        logging.info("Wait 'ready' from server ...")
        while True:
            await asyncio.sleep(.1)
            response = await mq_socket.recv_json()
            if response.get('msg_type', None) == MessageInType.READY:
                msg_payload = response['payload']
                ready_msg = ReadyMsg(**msg_payload)
                logging.info(f"Received 'ready' from server. Current agent_id:{ready_msg.your_agent_id}")
                return ready_msg

    async def handle_game_round(self, mq_socket: zmq.Socket, agent: BaseAgent):
        while True:
            json_data = await mq_socket.recv_json()
            msg_type = json_data.get('msg_type', None)
            payload = json_data.get('payload', None)
            logging.debug("Received from server: %s",json_data)
            if msg_type and payload:
                if msg_type == MessageInType.COMPLETE:
                    logging.info("Received 'complete' from server")
                    return
                elif msg_type == MessageInType.OFFER_REQUEST:
                    offer_request = OfferRequest(**payload)
                    agent_offer = agent.offer_action(offer_request)
                    await self.send_offer(mq_socket, agent_offer)
                elif msg_type == MessageInType.DEAL_REQUEST:
                    deal_request = DealRequest(**payload)
                    deal_result = agent.deal_action(deal_request)
                    await self.send_deal_result(mq_socket, deal_result)
                elif msg_type == MessageInType.ROUND_RESULT:
                    round_result = RoundResult(**payload)
                    agent.round_result_action(round_result)
                else:
                    logging.warning(f"Unexpected message type {msg_type}")
            else:
                raise Exception(f"Unexpected message json format: {json_data}")

    async def send_offer(self, mq_socket: zmq.Socket, agent_offer: int):
        msg = MessageOut(MessageOutType.OFFER_RESPONSE, OfferResponse(agent_offer))
        logging.info(f"Send 'offer' {msg} to server")
        await mq_socket.send_json(dataclasses.asdict(msg))

    async def send_deal_result(self, mq_socket: zmq.Socket, deal_result: bool):
        msg = MessageOut(MessageOutType.DEAL_RESPONSE, DealResponse(deal_result))
        logging.info(f"Send 'deal' {msg} to server")
        await mq_socket.send_json(dataclasses.asdict(msg))


if __name__ == '__main__':
    init_stdout_logging()
    client = Client()
    client.start()
