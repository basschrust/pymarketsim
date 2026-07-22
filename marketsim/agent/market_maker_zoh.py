import random
from decimal import Decimal
from marketsim.agent.agent import Agent
from marketsim.market.market import Market, Price
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
    def __init__(self, *, market: Market, agent_id: int=None, xi: float= 0.1,
                 K: int = 3, omega: float= 0.1, rebalance_period: int=5):

        self.agent_id = agent_id if agent_id is not None else id_generator.next()
        self.market = market

        self.position = 0
        self.cash = 0

        self.xi = Decimal(xi) # step of the order ladder
        self.K = K # number of orders in the ladder
        self.omega = Decimal(omega) # bid ask spread between two closest MM quotations
        self.rebalance_period = rebalance_period

    def get_id(self) -> int:
        return self.agent_id


    def is_market_maker(self) -> bool:
        return True


    def take_action(self, current_time: int):
        orders = []
        #t = self.market.get_time()
        # add orders only in rebalance periods:
        if current_time % self.rebalance_period == 0:
            # AK - clear previous orders (should we?)
            print(f"Withdrawing previous orders ()") # how to check number of orders of this agent?
            self.market.withdraw_all(self.agent_id)
            # AK - don't withdraw, but also don't blindly add new orders - just ensure they are balanced
            # that's basically the same to just withdraw all and create new, the problem might be with timing
            # - we could loose the slot in the queue of waiting orders

            # Get the best bid and best ask
            best_ask = self.market.order_book.get_best_ask()
            best_bid = self.market.order_book.get_best_bid()

            print(f"Best ask: {best_ask}, Best bid {best_bid}")

            estimate = self.market.last_traded_price
            HALF = Decimal("0.5")
            st = max(estimate + HALF * self.omega, best_bid)
            bt = min(estimate - HALF * self.omega, best_ask)


            for k in range(self.K):
                orders.append(
                    Order(
                        price= Price(bt - (k + 1) * self.xi),
                        quantity=1, # we ćould raise the quantity in each ladder step...
                        agent_id=self.agent_id,
                        time=current_time,
                        order_type=BUY,
                    )
                )
                orders.append(
                    Order(
                        price= Price(st + (k + 1)*self.xi),
                        quantity=1,
                        agent_id=self.agent_id,
                        time=current_time,
                        order_type=SELL,
                    )
                )

        return orders


    def get_pos_value(self) -> float:
        return 0

    def __str__(self):
        return f'MM_ZOH{self.agent_id}'

