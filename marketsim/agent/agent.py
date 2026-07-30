from abc import ABC, abstractmethod
import math
from typing import List
from dataclasses import dataclass, field

from marketsim.fourheap.order import Order
from marketsim.market.price import Price


def validate_update(quantity: int, cash: float) -> None:
    if not math.isfinite(cash):
        raise ValueError(f"cash must be finite (not NaN or ±inf) as here: {cash}")

    if quantity <= 0:
        if cash < 0:
            raise ValueError("Cash cannot be negative if quantity is negative!")

    if quantity >= 0:
        if cash > 0:
            raise ValueError("Cash cannot be positive if quantity is positive!")


class Agent(ABC):
    position = 0
    cash = 0
    trade_history = {} # dict of lists {day: [trades over that day]}
    # position_value_history = {0:0} # fill after every clearing
    # position_value_history: dict[int, Price] = field(default_factory=dict) # works in dataclasses only

    def __init__(self):
        self.position_value_history = {}

    @abstractmethod
    def get_id(self) -> int:
        pass

    @abstractmethod
    def take_action(self, current_time: int) -> List[Order]:
        pass

    @abstractmethod
    def get_pos_value(self) -> float:
        pass

    def update_position(self, quantity: int, cash: float) -> None:
        validate_update(quantity=quantity, cash=cash)
        self.position += quantity
        self.cash += cash

    def reset(self) -> None:
        self.position = 0
        self.cash = 0

    def is_market_maker(self) -> bool:
        return False

    def record_valuation(self, current_time: int, price: Price) -> None:
        self.position_value_history[current_time] = self.cash + self.position*price
