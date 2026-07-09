import random
from marketsim.agent.agent import Agent
from marketsim.market.market import Market
from marketsim.fourheap.order import Order
from marketsim.private_values.private_values import PrivateValues
from marketsim.fourheap.constants import BUY, SELL
from typing import List
from marketsim.utils.id_generator import id_generator


class MMZOHAgent(Agent):
    ### Market Maker Zero Order Hold Agent -
    # A MM which just takes into account last traded price and sets new order ladder
    # symmetrically on both sides of this last traded price in each rebalance period
    ###
    def __init__(self, agent_id: int, market: Market, xi: float,
                 K: int, omega: float, rebalance_period: int=2):
        self.agent_id = agent_id
        self.market = market

        self.position = 0
        self.cash = 0

        self.xi = xi # step of the order ladder
        self.K = K # number of orders in the ladder
        self.omega = omega
        self.rebalance_period = rebalance_period

    def get_id(self) -> int:
        return self.agent_id

    def take_action(self):
        orders = []
        t = self.market.get_time()
        # add orders only in rebalance periods:
        if t % self.rebalance_period == 0:

            # Get the best bid and best ask
            best_ask = self.market.order_book.get_best_ask()
            best_bid = self.market.order_book.get_best_bid()

            estimate = (best_ask + best_bid) /2 # or takse last traded, but yet the market does not "publish" it
            st = max(estimate + 1 / 2 * self.omega, best_bid)
            bt = min(estimate - 1 / 2 * self.omega, best_ask)


            for k in range(self.K):
                orders.append(
                    Order(
                        price= bt - (k + 1) * self.xi,
                        quantity=1, # we ćould raise the quantity in each ladder step...
                        agent_id=self.agent_id,
                        time=t,
                        order_type=BUY,
                    )
                )
                orders.append(
                    Order(
                        price= st + (k + 1)*self.xi,
                        quantity=1,
                        agent_id=self.agent_id,
                        time=t,
                        order_type=SELL,
                    )
                )

        return orders


    def get_pos_value(self) -> float:
        return 0

    def __str__(self):
        return f'MM{self.agent_id}'

