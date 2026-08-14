from abc import ABC, abstractmethod
import math
from typing import List
from dataclasses import dataclass, field
import traceback

from marketsim.fourheap.order import Order, MatchedOrder
from marketsim.market.price import Price
from marketsim.market import Market


def validate_update(quantity: int, cash: Price) -> None:
    if not math.isfinite(cash):
        raise ValueError(f"cash must be finite (not NaN or ±inf) as here: {cash}")

    if quantity <= 0:
        if cash < 0:
            raise ValueError("Cash cannot be negative if quantity is negative!")

    if quantity >= 0:
        if cash > 0:
            raise ValueError("Cash cannot be positive if quantity is positive!")


class Agent(ABC):
    # An agent is an investor operating on single market (investing in single security against their cash)

    def __init__(self, market: Market):
        self.trade_history = {}  # dict of lists/dicts {time: [trades over that day, volume bought, volume sold]}
        self.position_value_history = {} # {time: position_value}
        self.position_history = {0:0}  # {time: number_of_shares} # at the end of tick
        self.position = 0
        self._cash = Price(0)
        self.logger = market.logger

    @property
    def cash(self):
        return self._cash

    @cash.setter
    def cash(self, value):
        # print(f"Agent {id(self)} cash: {self._cash} -> {value}")
        # traceback.print_stack(limit=2)
        self._cash = value

    @abstractmethod
    def get_id(self) -> int:
        pass

    @abstractmethod
    def take_action(self, current_time: int) -> List[Order]:
        pass

    @abstractmethod
    def get_pos_value(self) -> float:
        pass

    def update_position(self, quantity: int, cash: Price) -> None:
        validate_update(quantity=quantity, cash=cash)
        self.position += quantity
        self.cash += cash

    def reset(self) -> None:
        self.position = 0
        self.cash = 0

    def is_market_maker(self) -> bool:
        return False

    def record_valuation(self, current_time: int, price: Price) -> None:
        self.position_history[current_time] = self.position
        self.position_value_history[current_time] = self.cash + self.position*price

    def record_trade(self, matched_order: MatchedOrder) -> None:
        quantity = matched_order.order.order_type * matched_order.order.quantity
        cash = -matched_order.price * matched_order.order.quantity * matched_order.order.order_type
        # print(f"Updating cash: {cash}")
        self.update_position(quantity=quantity, cash=cash)
        self.position_history[matched_order.time] = self.position_history.get(matched_order.time, 0) + quantity

        if matched_order.time in self.trade_history:
            # just add info
            old = self.trade_history.get(matched_order.time, {})
            self.trade_history[matched_order.time] = {"trades": old["trades"]+1,
                                                               "volume": old["volume"] + abs(matched_order.order.quantity),}
        else:
            # first trade this day
            self.trade_history[matched_order.time] = {"trades": 1, "volume": abs(matched_order.order.quantity),
                                                    } # side, volume bought/sold, ...

