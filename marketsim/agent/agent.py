from abc import ABC, abstractmethod
from marketsim.fourheap.order import Order
from typing import List


class Agent(ABC):
    position = 0
    cash = 0


    @abstractmethod
    def get_id(self) -> int:
        pass

    @abstractmethod
    def take_action(self) -> List[Order]:
        pass

    def get_pos_value(self) -> float:
        pass

    def update_position(self, q, p):
        self.position += q
        self.cash += p

    def reset(self):
        self.position = 0
        self.cash = 0

