from agent.base import BaseAgent
from base.protocol import OfferRequest, OfferResponse, DealRequest, DealResponse


class DummyAgent(BaseAgent):

    def __init__(self, my_name: str):
        self.my_name = my_name

    def get_my_name(self) -> str:
        return self.my_name

    def offer_action(self, m: OfferRequest) -> OfferResponse:
        return OfferResponse(m.total_amount // 2)

    def deal_action(self, m: DealRequest) -> DealResponse:
        if m.offer > 0:
            return DealResponse(True)
        else:
            return DealResponse(False)
