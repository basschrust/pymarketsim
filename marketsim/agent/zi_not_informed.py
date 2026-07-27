import random
from decimal import Decimal
from marketsim.agent.agent import Agent
from marketsim.market.market import Market
from marketsim.fourheap.order import Order
from marketsim.private_values.private_values import PrivateValues
from marketsim.fourheap.constants import BUY, SELL
from typing import List
import numpy as np
from marketsim.utils.id_generator import id_generator
from marketsim.market.price import Price


class ZIAgentNotInformed(Agent):
    def __init__(self, market: Market, q_max: int, shade: List, pv_var: float, eta: float = 1.0
                 , lam=1.0, mean_volume: float = 5.0):
        self.agent_id = id_generator.next()
        self.market = market
        self.q_max = q_max
        self.pv_var = pv_var
        # print(f"q_max: {self.q_max}, pv_var: {self.pv_var}")
        self.pv = PrivateValues(q_max, float(pv_var))
        self.position = 0
        self.shade = shade
        # print(f"shade: {self.shade}")
        self.cash = 0
        self.eta = eta
        #self._order_counter = 0  # Counter for unique order IDs (faster than random.randint)
            # not used any more, but maybe we want to count the orders placed by each agent
        self.lam = lam # activity parameter
        self.mean_volume = mean_volume

    def get_id(self) -> int:
        return self.agent_id

    def estimate_fundamental(self, current_time: int) -> Price:
        estimate = self.market.last_traded_price
        print(f'It is time {current_time} with final I observed last traded price {estimate}, so my estimate is {estimate}')
        return estimate

    def take_action(self, current_time: int, estimate: Price = None):
        orders = []
        if random.random() < self.lam:
            side = random.choice([BUY, SELL])
            quantity = np.random.poisson(lam=self.mean_volume) # AK why not volume?
            quantity = 3 if side == BUY else 5 # just for tests

            if estimate is None:
                estimate = Price(self.estimate_fundamental(current_time=current_time))
                #print(f"The estimate: {estimate}")
                #print(f"Private values: {self.pv.values}")
            spread = Decimal(self.shade[1] - self.shade[0])
            valuation_offset = Price(spread*Decimal(random.random())+ Decimal(self.shade[0]))

            # Cache private value lookup (avoid duplicate computation when eta != 1.0)
            pv_value = Price(self.pv.value_for_exchange(self.position, side))

            if side == BUY:
                price = estimate + pv_value - valuation_offset
                #AK: print(f"price: {price}, estimate: {estimate}, pv_value: {pv_value},  valuation_offset: {valuation_offset}")
            else:
                price = estimate + pv_value + valuation_offset

            if self.eta != 1.0:
                base_price = estimate + pv_value
                if side == BUY:
                    best_price = self.market.order_book.get_best_ask()
                    if (base_price - best_price) > self.eta*valuation_offset and best_price != np.inf:
                        price = best_price
                else:
                    best_price = self.market.order_book.get_best_bid()
                    if (best_price - base_price) > self.eta*valuation_offset and best_price != np.inf:
                        price = best_price

            if price > 0:
                order = Order(
                    price=Price(price),
                    quantity=quantity,
                    agent_id=self.agent_id,
                    time=current_time,
                    order_type=side,
                )
                orders.append(order)
            else:
                print(f"Order not placed as calculated price was negative: {price}, q: {quantity}")

        return orders


    def __str__(self) -> str:
        return f'ZI_non_informed{self.agent_id}'
        # TODO: AK to info func: with PVs: {self.pv.values}'

    def get_pos_value(self) -> float:
        return self.pv.value_at_position(self.position)

    def reset(self) -> None:
        self.position = 0
        self.cash = 0
        self.pv = PrivateValues(self.q_max, self.pv_var)
        self._order_counter = 0

