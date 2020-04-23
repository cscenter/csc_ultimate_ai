from abc import ABC, abstractmethod
from typing import cast, Optional, Dict

from base.protocol import MessageOut, MessageIn, Pong, MessageInType, PingMsg, OfferRequest, OfferResponse, \
    DealRequest, DealResponse, MessageOutType, RoundResult


# Agent 'interface'
class BaseAgent(ABC):
    agent_id: Optional[int] = None

    @staticmethod
    def get_my_name(self) -> str:
        pass

    @abstractmethod
    def offer_action(self, data: OfferRequest) -> int:
        # return your offer
        pass

    @abstractmethod
    def deal_action(self, data: DealRequest) -> bool:
        # return True if you accept offer False otherwise
        pass

    @abstractmethod
    def round_result_action(self, data: RoundResult):
        # Round statistics
        pass
