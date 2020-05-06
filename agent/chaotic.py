import random

from agent.base import BaseAgent
from base.protocol import OfferRequest, OfferResponse, DealRequest, DealResponse, RoundResult


class ChaoticAgent(BaseAgent):

    def offer_action(self, data: OfferRequest) -> int:
        return random.randint(0, data.total_amount)

    def deal_action(self, data: DealRequest) -> bool:
        return random.choice([True, False])

    def round_result_action(self, data: RoundResult):
        pass
