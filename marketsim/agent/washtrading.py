import math
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
        super().__init__(market=market)
        self.group = "WASH_TRADING"
        self.agent_id = id_generator.next()
        self.market = market # TODO: needed here if passed to super?
        self.q_max = q_max
        self.lam = lam # yet not used - probably used in the non-manipulation period
        self.position = 0
        self.cash = 0
        self.pool_id = pool_id
        self.manipulation_boundaries = manipulation_boundaries # what if several such periods? maybe list of dicts?
        self.mean_volume = mean_volume
        # specific for this (WashTrading) type:
        self.price_to_reach = self.market.last_traded_price
        self.quantity = 0


    def get_id(self) -> int:
        return self.agent_id


    def take_action(self, current_time: int): #, estimate: Price|None=None):
        #self.market.withdraw_all(agent_id=self.agent_id) # no! we have to leave it for the crossing with the
            # WT on the other side!
        period = self.manipulation_boundaries["manipulation_period"]
        orders = []

        if period["start"] <= current_time <= period["end"]:
            # so act as designed
            length = max(period["end"] - current_time + 1, 10)  # how many days left in the manipulation period
            # print(f"WASHTRADER: q_max: {self.q_max}, position: {self.position}, length: {length}, lambda: {self.lam}, price: {price}")

            # if q_max almost reached we could try to push more with spread?
            if self.manipulation_boundaries["lam"] > random.random(): # let's see what happens when we push always
                # but then this method is easy to find out
                #withdraw his old orders if yet not exercised
                #self.market.withdraw_all(agent_id=self.agent_id)
                # TODO: if the position is heavily unbalanced set more aggressive price, too
                if current_time % 3 == 1:
                    # in odd time ticks calculate volume & price and make order of one side
                    self.market.withdraw_all(agent_id=self.agent_id) # cancel also only in odd ticks

                    if self.manipulation_boundaries["manipulation_type"] == "PULL_UP":
                        self.quantity = int(
                            (self.q_max - abs(self.position)) / (length * self.manipulation_boundaries["lam"]))
                        # TODO: check if this liquidity check gives the reached or exceeded volumes (what happens on boundaries)
                        self.price_to_reach = self.market.order_book.get_ask_at_volume(
                            self.quantity / 4)  # + Price(0.01)

                        if not math.isfinite(self.price_to_reach):
                            self.price_to_reach = self.market.last_traded_price + Price(0.5)

                        if self.manipulation_boundaries["manipulation_side"] == "BUY":
                            if self.price_to_reach > 0 and self.quantity > 0:
                                order = Order(
                                    price=self.price_to_reach,
                                    quantity=self.quantity,
                                    agent_id=self.agent_id,
                                    asset_id=self.market.asset_id,
                                    time=current_time,
                                    order_type=1 if self.manipulation_boundaries["manipulation_side"] == 'BUY' else -1,
                                )
                                orders.append(order)
                                return orders
                        else:
                            self.price_to_reach = max(self.price_to_reach - Price(0.01), Price(0.01))

                    elif self.manipulation_boundaries.get("manipulation_type") == "PUSH_DOWN":
                        self.quantity = int(
                            (self.q_max - abs(self.position)) / (length * self.manipulation_boundaries["lam"]))
                        self.price_to_reach = self.market.order_book.get_bid_at_volume(self.quantity / 4)
                        # TODO: add also a memory what price we set in the previous step (and was the order executed?)
                        # TODO: and matched with the other side of the WT or just MM or Noise?
                        if math.isfinite(self.price_to_reach):
                            self.price_to_reach = self.price_to_reach  # - Price(0.01)
                        else:
                            self.price_to_reach = max(self.market.last_traded_price - Price(0.5), Price(0.01))

                        if self.manipulation_boundaries["manipulation_side"] == "BUY":
                            self.price_to_reach = self.price_to_reach+Price(0.01)
                        else:
                            if self.price_to_reach > 0 and self.quantity > 0:
                                order = Order(
                                    price=self.price_to_reach,
                                    quantity=self.quantity,
                                    agent_id=self.agent_id,
                                    asset_id=self.market.asset_id,
                                    time=current_time,
                                    order_type=1 if self.manipulation_boundaries["manipulation_side"] == 'BUY' else -1,
                                )
                                orders.append(order)
                                return orders

                    else:
                        raise ValueError(f"Invalid manipulation type {self.manipulation_boundaries['manipulation_type']}")
                elif current_time % 3 == 2:
                    # in even time ticks (2/3) place the other side order, use price and volume calculated in previous step
                    if self.manipulation_boundaries["manipulation_type"] == "PULL_UP":
                        if self.manipulation_boundaries["manipulation_side"] == "BUY":
                            self.quantity = 0
                        else:
                            if self.price_to_reach > 0 and self.quantity > 0:
                                order = Order(
                                    price=self.price_to_reach,
                                    quantity=self.quantity,
                                    agent_id=self.agent_id,
                                    asset_id=self.market.asset_id,
                                    time=current_time,
                                    order_type=1 if self.manipulation_boundaries["manipulation_side"] == 'BUY' else -1,
                                )
                                orders.append(order)

                    elif self.manipulation_boundaries["manipulation_type"] == "PUSH_DOWN":
                        if self.manipulation_boundaries["manipulation_side"] == "SELL":
                            self.quantity = 0
                        else:
                            if self.price_to_reach > 0 and self.quantity > 0:
                                order = Order(
                                    price=self.price_to_reach,
                                    quantity=self.quantity,
                                    agent_id=self.agent_id,
                                    asset_id=self.market.asset_id,
                                    time=current_time,
                                    order_type=1 if self.manipulation_boundaries["manipulation_side"] == 'BUY' else -1,
                                )
                                orders.append(order)

                    else:
                        raise ValueError(
                            f"Invalid manipulation type {self.manipulation_boundaries['manipulation_type']}")
                else:
                    self.logger.info(f"WT waiting turn in time {current_time}.")

        else:
            # TODO: be a normal ZI agent :)  (sometimes smoothly align position using PVs)
            if random.random() < self.lam:
                # but if we are after washtrading then let's try to rebalance as much as we can
                # so let only one side of the orders
                if current_time < period["start"]:
                    side = random.choice([BUY, SELL])
                    quantity = np.random.poisson(lam=self.mean_volume) if abs(self.position) < self.q_max else 1
                else:
                    # so we are after the manipulation period - let's just rebalance here
                    side = 1 if self.manipulation_boundaries["manipulation_side"] == 'BUY' else -1
                    # but how not to exceed the q_max? - like this:   # but we don't know how many steps are left
                        # till the end of the simulation, it should depend on the momentary liquidity
                    quantity = int((self.q_max - abs(self.position)) * (0.5 + 0.5 *random.random()) / 30)

                spread = self.manipulation_boundaries["spread"] # maybe some other spread should be put here
                # TODO: some rebalance spread parameter?
                price = self.market.last_traded_price + Price(0.05 * spread * (random.random() - 0.5))

                if price > 0 and quantity > 0:
                    order = Order(
                        price=price,
                        quantity=quantity,
                        agent_id=self.agent_id,
                        asset_id=self.market.asset_id,
                        time=current_time,
                        order_type=side,
                    )
                    orders.append(order)
        return orders

    def __str__(self):
        return f'WT_{self.pool_id}_{self.agent_id}'

    def reset(self):
        self.position = 0
        self.cash = 0

    def get_pos_value(self) -> float:
        return 0


class WashTradingPool:
    def __init__(self, market: Market, pool_id: int, manipulation_type: str, manipulation_start: int, manipulation_end: int):
        # TODO: maybe we could store a reciprocal hook in each of those agents in the pool so that they can
        # check the balance of each other and push their position towards equilibrium?
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



