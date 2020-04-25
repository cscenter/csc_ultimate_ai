from agent.base import BaseAgent
from base.protocol import OfferRequest, OfferResponse, DealRequest, DealResponse, RoundResult


class CheaterAgent(BaseAgent):

    def get_my_name(self) -> str:
        return 'Cheater'

    def offer_action(self, m: OfferRequest) -> int:
        return min(m.total_amount, 1)

    def deal_action(self, m: DealRequest) -> bool:
        if m.offer > 0:
            return True
        else:
            return False

    def round_result_action(self, data: RoundResult):
        pass

