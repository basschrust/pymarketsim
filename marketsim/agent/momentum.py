import random

from marketsim.agent.agent import Agent
from marketsim.market.market import Market, Price
from marketsim.fourheap.order import Order
from marketsim.fourheap.constants import BUY, SELL
from marketsim.utils.id_generator import id_generator


class MomentumAgent(Agent):
    ### Momentum Agent -
    # Momentum Agent trades using moving average to catch the market trend
    ###
    def __init__(self, *, market: Market, agent_id: int | None=None, period: int=7, lam: float= 0.5, q_max: int=100, threshold: float=0.01):
        super().__init__(market=market)
        self.group = "MOMENTUM"
        self.agent_id = agent_id if agent_id is not None else id_generator.next()
        self.market = market # could agent serve multiple markets?
        self.period = period # the period for trend analyzing
        self.lam = lam # lambda, the activity parameter
        self.q_max = q_max # maximum agent position on each side
        self.threshold = threshold # threshold above which we consider the trend to exist
        self.position = 0
        self.cash = 0


    def get_id(self) -> int:
        return self.agent_id


    def is_market_maker(self) -> bool:
        return False

    def take_action(self, current_time: int):
        orders = []
        # compute the momentum
        # compare last traded price (in t-1 - or maybe current last traded?) with price period ticks ago (why not MA?)
        # if price[t-1] > (1+threshold) * price[t-period] -> buy
        # if price[t-1] < (1-threshold) * price[t-period] -> sell
        # amounts? and lambda? yet ignore, take into account in next iteration, price limit?
        if current_time >= self.period:
            self.market.withdraw_all(agent_id=self.agent_id)
            previous_price = self.market.traded_prices[current_time-self.period]["Close"]
            limit = Price(float(self.market.last_traded_price) * (0.95 + 0.1*random.uniform(0, 1)))
            # asymptotic approaching the q_max - but let it also reverse the trend when position is high...
            if self.market.last_traded_price > float(previous_price) * (1+self.threshold):
                if self.position > 0:
                    # asymptotic approach
                    quantity = int(self.q_max - abs(self.position) / 10)
                else:
                    # reversing the trend
                    quantity = int(self.q_max / 10)
                if quantity > 0:
                    orders.append(
                        Order(
                            price=limit,
                            quantity=quantity,
                            agent_id=self.agent_id,
                            time=current_time,
                            order_type=BUY,
                            asset_id=self.market.asset_id,
                        )
                    )
            elif self.market.last_traded_price < float(previous_price) * (1-self.threshold):
                if self.position < 0:
                    # asymptotic approach
                    quantity = int(self.q_max - abs(self.position) / 10)
                else:
                    # reversing the trend
                    quantity = int(self.q_max / 10)
                if quantity > 0:
                    orders.append(
                        Order(
                            price=limit,
                            quantity=quantity,
                            agent_id=self.agent_id,
                            time=current_time,
                            order_type=SELL,
                            asset_id=self.market.asset_id,
                        )
                    )

        return orders


    def get_pos_value(self) -> float:
        return 0

    def __str__(self):
        return f'Momentum_{self.agent_id}'

