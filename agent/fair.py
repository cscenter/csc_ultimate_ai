from agent.base import BaseAgent
from base.protocol import OfferRequest, OfferResponse, DealRequest, DealResponse, RoundResult


class FairAgent(BaseAgent):

    def offer_action(self, m: OfferRequest) -> int:
        return m.total_amount // 2

    def deal_action(self, m: DealRequest) -> bool:
        if m.offer >= m.total_amount // 2:
            return True
        else:
            return False

    def round_result_action(self, data: RoundResult):
        pass

