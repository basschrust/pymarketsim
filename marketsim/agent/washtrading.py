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


    def take_action(self, current_time: int): #, estimate: Price|None=None):
        self.market.withdraw_all(agent_id=self.agent_id)
        period = self.manipulation_boundaries["manipulation_period"]
        orders = []

        if period["start"] <= current_time <= period["end"]:
            # so act as designed
            best_bid = self.market.order_book.buy_unmatched.peek()
            best_ask = self.market.order_book.sell_unmatched.peek()
            if not math.isfinite(best_bid):
                best_bid = self.market.last_traded_price - Price(0.01)
            if not math.isfinite(best_ask):
                best_ask = self.market.last_traded_price + Price(0.01)
            #price = estimate if estimate is not None else self.market.last_traded_price
            length = period["end"] - current_time + 1  # how many days left in the manipulation period
            # print(f"WASHTRADER: q_max: {self.q_max}, position: {self.position}, length: {length}, lambda: {self.lam}, price: {price}")

            # if q_max almost reached we could try to push more with spread?
            if True: #self.manipulation_boundaries["lam"] > random.random(): # let's see what happens when we push always
                #withdraw his old orders if yet not exercised
                self.market.withdraw_all(agent_id=self.agent_id)
                # TODO: if the position is heavily unbalanced set more aggressive price, too
                if self.manipulation_boundaries["manipulation_type"] == "PULL_UP":
                    #price = price + Price((self.manipulation_boundaries["spread"]*(0.9 + 0.2 * random.random())))

                    price = Price(best_ask) # or just below it? or randomly very close?
                    if self.manipulation_boundaries["manipulation_side"] == "BUY":
                        quantity = int(
                            (self.q_max - abs(self.position)) / (length * self.manipulation_boundaries["lam"]))

                    else:
                        # it was hard to set the proper volume here, the position kept being unbalanced so we have to sell more quickly
                        quantity = int(
                            (self.q_max - abs(self.position)) * 1 / (length * self.manipulation_boundaries["lam"]))
                    price_to_reach = self.market.order_book.get_ask_at_volume(quantity / 4)
                    if not math.isfinite(price_to_reach):
                        price_to_reach = self.market.last_traded_price + Price(0.5)
                elif self.manipulation_boundaries.get("manipulation_type") == "PUSH_DOWN":
                    # prevent price from falling below 0:
                    # TODO: check if this is not the reason the market falls down systematically - the spread should
                    # lead to lognormal in long term.
                    #price = max(Price((float(price) - self.manipulation_boundaries["spread"])*(0.98 + 0.04 * random.random())), Price(0.01))
                    price = Price(best_bid) # if the edge is weak we could push further by bigger order
                    if self.manipulation_boundaries["manipulation_side"] == "BUY":
                        quantity = int(
                            (self.q_max - abs(self.position)) * 1 / (length * self.manipulation_boundaries["lam"]))
                    else:
                        quantity = int(
                            (self.q_max - abs(self.position)) / (length * self.manipulation_boundaries["lam"]))
                    price_to_reach = self.market.order_book.get_bid_at_volume(quantity / 4)
                    if not math.isfinite(price_to_reach):
                        price_to_reach = max(self.market.last_traded_price - Price(0.5), Price(0.01))
                else:
                    raise ValueError(f"Invalid manipulation type {self.manipulation_boundaries['manipulation_type']}")

                if length < (period["end"] - period["start"]) / 2:
                    # in the second half we push more on volume to properly balance the position
                    quantity = int(1.2 * quantity)

                # the order should be placed with price within the boundaries specified by the venue
                #if  price_to_reach

                if price_to_reach > 0 and quantity > 0:
                    order = Order(
                        price=price_to_reach,
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



