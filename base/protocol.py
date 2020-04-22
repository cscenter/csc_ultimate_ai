import uuid
from dataclasses import dataclass, field
from enum import Enum
from abc import ABC
from typing import Dict
import time


# # # # # # # # # #
# Input messages  #
# # # # # # # # # #

class MessageInType(str, Enum):
    PING = 'PING'
    READY = 'READY'
    OFFER_REQUEST = 'OFFER_REQUEST'
    DEAL_REQUEST = 'DEAL_REQUEST'
    ROUND_RESULT = 'ROUND_RESULT'


class MessageInPayload(ABC):
    pass


@dataclass(eq=True, frozen=True)
class PingMsg(MessageInPayload):
    timestamp: float = field(default_factory=lambda: time.time())


@dataclass(eq=True, frozen=True)
class ReadyMsg(MessageInPayload):
    your_agent_id: int


@dataclass(eq=True, frozen=True)
class OfferRequest(MessageInPayload):
    round_id: int
    target_agent_id: int
    total_amount: int


@dataclass(eq=True, frozen=True)
class DealRequest(MessageInPayload):
    round_id: int
    from_agent_id: int
    total_amount: int
    offer: int


@dataclass(eq=True, frozen=True)
class RoundResult(MessageInPayload):
    round_id: int
    win: bool
    agent_gain: Dict[int, int]


@dataclass(eq=True, frozen=True)
class MessageIn:
    msg_type: MessageInType
    payload: MessageInPayload


# # # # # # # # # #
# Output messages #
# # # # # # # # # #

class MessageOutType(str, Enum):
    HELLO = 'HELLO'
    PONG = 'PONG'
    OFFER_RESPONSE = 'OFFER_RESPONSE'
    DEAL_RESPONSE = 'DEAL_RESPONSE'


class MessageOutPayload(ABC):
    pass


@dataclass(eq=True, frozen=True)
class Hello(MessageOutPayload):
    my_name: str


@dataclass(eq=True, frozen=True)
class Pong(MessageOutPayload):
    timestamp: float = field(default_factory=lambda: time.time())


@dataclass(eq=True, frozen=True)
class OfferResponse(MessageOutPayload):
    offer: int


@dataclass(eq=True, frozen=True)
class DealResponse(MessageOutPayload):
    accepted: bool


@dataclass(eq=True, frozen=True)
class MessageOut:
    msg_type: MessageOutType
    payload: MessageOutPayload
