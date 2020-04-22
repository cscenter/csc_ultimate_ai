import asyncio
import dataclasses
import uuid

import dataclass_factory
import zmq.asyncio
from zmq.asyncio import Context
import traceback
import logging

from base.protocol import Hello, MessageOut, MessageOutType
from base.util import init_stdout_logging

init_stdout_logging()

url = '127.0.0.1'
port = '5555'
url = "tcp://{}:{}".format(url, port)
# pub/sub and dealer/router
ctx = Context.instance()
factory = dataclass_factory.Factory()
connection_uid = str(uuid.uuid4())


async def client_handler():
    # setup dealer
    deal = ctx.socket(zmq.DEALER)
    deal.setsockopt(zmq.IDENTITY, bytes(connection_uid, 'utf-8'))
    deal.connect(url[:-1] + "{}".format(int(url[-1]) + 1))
    logging.info(f"Client dealer initialized uid:{connection_uid}")

    # give time to router to initialize; wait time >.2 sec
    await asyncio.sleep(.3)

    try:
        msg = MessageOut(MessageOutType.HELLO, Hello("Vasia"))
        logging.info("Send 'hello' to server")
        await deal.send_json(dataclasses.asdict(msg))
        logging.info("Wait 'ready' from server ...")
        r = await deal.recv_multipart()
        print(r)

    except Exception as e:
        print("Error with pub world")
        # print(e)
        logging.error(traceback.format_exc())
        print()

    finally:
        # TODO disconnect dealer/router
        pass


asyncio.get_event_loop().run_until_complete(asyncio.wait([
    client_handler()]))
