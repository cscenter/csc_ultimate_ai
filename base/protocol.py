import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Optional


# # # # # # # # # #
# Input messages  #
# # # # # # # # # #

class MessageInType(str, Enum):
    PING = 'PING'
    READY = 'READY'
    COMPLETE = 'COMPLETE'
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
    your_agent_uid: str


@dataclass(eq=True, frozen=True)
class OfferRequest(MessageInPayload):
    round_id: int
    target_agent_uid: str
    total_amount: int


@dataclass(eq=True, frozen=True)
class DealRequest(MessageInPayload):
    round_id: int
    from_agent_uid: str
    total_amount: int
    offer: int


@dataclass(eq=True, frozen=True)
class RoundResult(MessageInPayload):
    round_id: int
    # True - if offer has been accepted
    win: bool
    # key - agent uid, value - round gain amount
    agent_gain: Dict[str, int]
    disconnection_failure: bool = False


@dataclass(eq=True, frozen=True)
class MessageIn:
    msg_type: MessageInType
    payload: Optional[MessageInPayload]


# # # # # # # # # #
# Output messages #
# # # # # # # # # #

class MessageOutType(str, Enum):
    HELLO = 'HELLO'
    PONG = 'PONG'
    OFFER_RESPONSE = 'OFFER_RESPONSE'
    DEAL_RESPONSE = 'DEAL_RESPONSE'


class MessageOutPayload(ABC):

    @abstractmethod
    def find_error(self) -> Optional[str]:
        pass


@dataclass(eq=True, frozen=True)
class Hello(MessageOutPayload):
    my_name: str

    def find_error(self) -> Optional[str]:
        if not self.my_name:
            return "Non empty 'my_name' required"
        if not isinstance(self.my_name, str):
            return "String type for 'my_name' required"


@dataclass(eq=True, frozen=True)
class Pong(MessageOutPayload):
    timestamp: float = field(default_factory=lambda: time.time())

    def find_error(self) -> Optional[str]:
        if not self.timestamp:
            return "Non empty 'timestamp' required"
        if not isinstance(self.timestamp, float):
            return "Float type for 'timestamp' required"
        if self.timestamp < 0:
            return "Non negative 'offer' required"


@dataclass(eq=True, frozen=True)
class OfferResponse(MessageOutPayload):
    offer: int

    def find_error(self) -> Optional[str]:
        if not self.offer:
            return "Non empty 'offer' required"
        if not isinstance(self.offer, int):
            return "Int type for 'offer' required"
        if self.offer < 0:
            return "Non negative 'offer' required"


@dataclass(eq=True, frozen=True)
class DealResponse(MessageOutPayload):
    accepted: bool

    def find_error(self) -> Optional[str]:
        if self.accepted is None:
            return "Non empty 'accepted' required"
        if not isinstance(self.accepted, bool):
            return "Bool type for 'accepted' required"


@dataclass(eq=True, frozen=True)
class MessageOut:
    msg_type: MessageOutType
    payload: Optional[MessageOutPayload]
