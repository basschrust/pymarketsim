import random
from typing import List
import numpy as np
from decimal import Decimal

from marketsim.agent.agent import Agent
from marketsim.market.market import Market, Price
from marketsim.fourheap.order import Order
from marketsim.private_values.private_values import PrivateValues
from marketsim.fourheap.constants import BUY, SELL
from marketsim.utils.id_generator import id_generator


class WashTradingAgent(Agent):
    def __init__(self, market: Market, q_max: int, lam: float = 0.5, pool_id: int = 0, manipulation_boundaries: dict = None, mean_volume: float = 5.0):
        super().__init__()
        self.group = "WASH_TRADING"
        self.agent_id = id_generator.next()
        self.market = market
        self.q_max = q_max
        self.lam = lam # yet not used
        self.position = 0
        self.cash = 0
        self.pool_id = pool_id
        self.manipulation_boundaries = manipulation_boundaries # what if several such periods? maybe list of dicts?
        self.mean_volume = mean_volume


    def get_id(self) -> int:
        return self.agent_id


    def take_action(self, current_time: int, estimate: Price|None=None):
        period = self.manipulation_boundaries["manipulation_period"]
        orders = []

        if period["start"] <= current_time <= period["end"]:
            # so act as designed
            price = estimate if estimate is not None else self.market.last_traded_price
            length = period["end"] - current_time + 1  # how many days left in the manipulation period
            # print(f"WASHTRADER: q_max: {self.q_max}, position: {self.position}, length: {length}, lambda: {self.lam}, price: {price}")
            quantity = int((self.q_max - abs(self.position)) / (length * self.manipulation_boundaries["lam"])) + 1
            if length < (period["end"] - period["start"])/2:
                # in the second half we push more on volume to properly balance the position
                quantity *= 2
            # if q_max almost reached we could try to push more with spread?
            if self.manipulation_boundaries["lam"] > random.random():
                #withdraw his old orders if yet not exercised
                self.market.withdraw_all(self.agent_id)
                # TODO: if the position is heavily unbalanced set more aggressive price, too
                if self.manipulation_boundaries["manipulation_type"] == "PULL_UP":
                    price = price + Price((self.manipulation_boundaries["spread"]*0.9 + 0.2 * random.random()))
                elif self.manipulation_boundaries["manipulation_type"] == "PUSH_DOWN":
                    price = price - Price((self.manipulation_boundaries["spread"]*0.9 + 0.2 * random.random()))
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
                orders.append(order)

        else:
            # TODO: be a normal ZI agent :)  (sometimes smoothly align position using PVs)
            if random.random() < self.lam:
                # but if we are after washtrading then let's try to rebalance as much as we can
                # so let only one side of the orders
                if current_time < period["start"]:
                    side = random.choice([BUY, SELL])
                else:
                    side = self.manipulation_boundaries["manipulation_side"]
                    # but how not to exceed the q_max?
                quantity = np.random.poisson(lam=self.mean_volume) if abs(self.position) < self.q_max else 1
                spread = 0.2 #  Decimal(self.shade[1] - self.shade[0])
                price = self.market.last_traded_price + Price(spread * random.random() + spread/2)

                order = Order(
                    price=price,
                    quantity=quantity,
                    agent_id=self.agent_id,
                    asset_id=self.market.asset_id,
                    time=current_time,
                    order_type=1 if side == 'BUY' else -1,
                )
                orders.append(order)
        return orders




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
        raise # as yet it's not used
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



