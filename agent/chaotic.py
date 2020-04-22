import random

from agent.base import BaseAgent
from base.protocol import OfferRequest, OfferResponse, DealRequest, DealResponse


class ChaoticAgent(BaseAgent):

    def __init__(self, my_name: str):
        self.my_name = my_name

    def get_my_name(self) -> str:
        return self.my_name

    def offer_action(self, m: OfferRequest) -> OfferResponse:
        return OfferResponse(random.randint(0, m.total_amount))

    def deal_action(self, m: DealRequest) -> DealResponse:
        return DealResponse(random.choice([True, False]))
