import random
from typing import List
import numpy as np

from marketsim.agent.agent import Agent
from marketsim.market.market import Market, Price
from marketsim.fourheap.order import Order
from marketsim.private_values.private_values import PrivateValues
from marketsim.fourheap.constants import BUY, SELL
from marketsim.utils.id_generator import id_generator


class WashTradingAgent(Agent):
    def __init__(self, market: Market, q_max: int, lam: float = 0.5, pool_id: int = 0, manipulation_boundaries: dict = None):
        super().__init__()
        self.agent_id = id_generator.next()
        self.market = market
        self.q_max = q_max
        self.lam = lam # yet not used
        self.position = 0
        self.cash = 0
        self.pool_id = pool_id
        self.manipulation_boundaries = manipulation_boundaries # what if several such periods? maybe list of dicts?


    def get_id(self) -> int:
        return self.agent_id


    def take_action(self, current_time: int, estimate: Price|None=None):
        price = estimate if estimate is not None else self.market.last_traded_price
        period = self.manipulation_boundaries["manipulation_period"]
        period_length = period["end"] - period["start"]
        till_end = period["end"] - current_time
        # TODO: please find the right volume (quantity) here, set proper parameters and their defaults
        # maybe not a single order but a bunch of them?
        # or create a series of orders and then just let them out to the queue one by one?
        # so just keep his own, local queue and put the orders from it to the market queue in proper time ticks
        # dividing q_max per number of orders is not enough - some of them might not be fulfilled
        quantity = int(self.q_max/5)
        #int((self.q_max - abs(self.position)+random.random())/(till_end + random.random()))

        if period["start"] <= current_time <= period["end"]:
            # so act as designed
            # TODO: add some randomness to the price limit, too
            if self.manipulation_boundaries["manipulation_type"] == "PULL_UP":
                price = price + Price(self.manipulation_boundaries["spread"])
            elif self.manipulation_boundaries["manipulation_type"] == "PUSH_DOWN":
                price = price - Price(self.manipulation_boundaries["spread"])
            else:
                raise ValueError(f"Invalid manipulation type {self.manipulation_boundaries['manipulation_type']}")

            order = Order(
                price=price,
                quantity=quantity,
                agent_id=self.agent_id,
                asset_id=self.market.asset_id,
                time=current_time,
                order_type=1 if self.manipulation_boundaries["manipulation_side"]=='BUY' else -1,
            )
            return [order]

        else:
            # be a normal ZI agent :)  (sometimes smoothly align position using PVs)
            pass
            return []




    def __str__(self):
        return f'WT_{self.pool_id}_{self.agent_id}'
            #f'WT_{self.manipulation_type}_{self.manipulation_side}_{self.pool_id}_{self.agent_id}'

    def reset(self):
        self.position = 0
        self.cash = 0

    def get_pos_value(self) -> float:
        return 0


class WashTradingPool:
    def __init__(self, market: Market, pool_id: int, manipulation_type: str, manipulation_start: int, manipulation_end: int):
        self.market = market
        self.id = pool_id
        self.type = manipulation_type # 'PULL_UP' or 'PUSH_DOWN'
        self.manipulation_start = manipulation_start # tau_1, manipulation starts here
        self.manipulation_end = manipulation_end # tau_2, manipulation ends here

    def get_id(self) -> int:
        return self.id

    def manipulation_start(self):
        # send signal to all agents in the pool
        pass



