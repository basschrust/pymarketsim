from abc import ABC, abstractmethod
import math
from typing import List
from marketsim.fourheap.order import Order


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
