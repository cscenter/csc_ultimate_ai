from agent.base import BaseAgent
from base.protocol import OfferRequest, OfferResponse, DealRequest, DealResponse


class DummyAgent(BaseAgent):

    def get_my_name(self) -> str:
        return 'Dummy'

    def offer_action(self, m: OfferRequest) -> OfferResponse:
        return OfferResponse(m.total_amount // 2)

    def deal_action(self, m: DealRequest) -> DealResponse:
        if m.offer > 0:
            return DealResponse(True)
        else:
            return DealResponse(False)
