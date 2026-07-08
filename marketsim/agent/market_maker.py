import random
from marketsim.agent.agent import Agent
from marketsim.market.market import Market
from marketsim.fourheap.order import Order
from marketsim.private_values.private_values import PrivateValues
from marketsim.fourheap.constants import BUY, SELL
from typing import List
from marketsim.utils.id_generator import id_generator


class MMAgent(Agent):
    def __init__(self, agent_id: int, market: Market, xi: float, K: int, omega: float, rebalance_period: int=5):
        self.agent_id = agent_id
        self.market = market

        self.position = 0
        self.cash = 0

        self.xi = xi
        self.K = K
        self.omega = omega
        self.rebalance_period = rebalance_period

    def get_id(self) -> int:
        return self.agent_id

    def estimate_fundamental(self):
        mean, r, T = self.market.get_info()
        t = self.market.get_time()
        val = self.market.get_fundamental_value()

        rho = (1-r)**(T-t)

        estimate = (1-rho)*mean + rho*val
        return estimate

    def take_action(self):
        orders = []
        t = self.market.get_time()
        # add orders only in rebalance periods:
        if t % self.rebalance_period == 0:

            # Get the best bid and best ask
            best_ask = self.market.order_book.get_best_ask()
            best_bid = self.market.order_book.get_best_bid()

            estimate = self.estimate_fundamental()
            st = max(estimate + 1 / 2 * self.omega, best_bid)
            bt = min(estimate - 1 / 2 * self.omega, best_ask)


            for k in range(self.K):
                orders.append(
                    Order(
                        price= bt - (k + 1) * self.xi,
                        quantity=1,
                        agent_id=self.get_id(),
                        time=t,
                        order_type=BUY,
                        order_id=id_generator.next()
                        #random.randint(1, 10000000)
                    )
                )
                orders.append(
                    Order(
                        price= st + (k + 1)*self.xi,
                        quantity=1,
                        agent_id=self.get_id(),
                        time=t,
                        order_type=SELL,
                        order_id=id_generator.next()
                        #random.randint(1, 10000000)
                    )
                )

        return orders

    def update_position(self, q, p):
        self.position += q
        self.cash += p

    def get_pos_value(self) -> float:
        return 0

    def __str__(self):
        return f'MM{self.agent_id}'

    def reset(self):
        self.position = 0
        self.cash = 0
