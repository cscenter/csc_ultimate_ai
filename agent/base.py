import random
from abc import ABC, abstractmethod
from typing import cast, Optional

from agent.protocol import MessageOut, MessageIn, Pong, MessageInType, PingMsg, OfferRequest, OfferResponse, \
    DealRequest, DealResponse, MessageOutType


# Agent 'interface'
class BaseAgent(ABC):
    agent_id: Optional[int] = None

    def action(self, m: MessageIn) -> MessageOut:
        if m.msg_type == MessageInType.PING:
            res_p = self.ping_action(cast(PingMsg, m))
            res_t = MessageOutType.PONG
        elif m.msg_type == MessageInType.OFFER_REQUEST:
            res_p = self.offer_action(cast(OfferRequest, m))
            res_t = MessageOutType.OFFER_RESPONSE
        elif m.msg_type == MessageInType.DEAL_REQUEST:
            res_p = self.deal_action(cast(DealRequest, m))
            res_t = MessageOutType.OFFER_RESPONSE
        else:
            raise Exception(f"Unexpected message type {m.msg_type}")
        return MessageOut(res_t, res_p)

    def ping_action(self, m: PingMsg) -> Pong:
        self.agent_id = m.agent_id
        return Pong()

    @abstractmethod
    def offer_action(self, m: OfferRequest) -> OfferResponse:
        pass

    @abstractmethod
    def deal_action(self, m: DealRequest) -> DealResponse:
        pass


class DummyAgent(BaseAgent):

    def offer_action(self, m: OfferRequest) -> OfferResponse:
        return OfferResponse(m.total_amount // 2)

    def deal_action(self, m: DealRequest) -> DealResponse:
        if m.offer > 0:
            return DealResponse(True)
        else:
            return DealResponse(False)


class ChaoticAgent(BaseAgent):

    def offer_action(self, m: OfferRequest) -> OfferResponse:
        return OfferResponse(random.randint(0, m.total_amount))

    def deal_action(self, m: DealRequest) -> DealResponse:
        return DealResponse(random.choice([True, False]))
