from dataclasses import dataclass

from marketsim.utils.id_generator import id_generator
from marketsim.market.price import Price

def validate_price(price: Price) -> None:
    if price <=0:
        raise ValueError('Price must be greater than 0')

@dataclass
class Order:
    price: Price
    order_type: int  # -1 for a sell order, +1 for a buy order
    quantity: int
    agent_id: int
    time: int
    order_id: int
    asset_id: int = 1

    def __init__(self, price: Price, order_type: int, quantity: int, agent_id: int, time:int):
        validate_price(price)
        self.price = price
        self.order_type = order_type
        self.quantity = quantity
        self.agent_id = agent_id
        self.time = time
        self.order_id = id_generator.next()

    def update_quantity_filled(self, transact_quantity: int) -> None:
        self.quantity -= transact_quantity

    def merge_order(self, q_additional: int) -> None:
        self.quantity += q_additional

    def copy_and_decrease(self, transact_quantity: int) -> 'Order':
        new_order = Order(price=self.price,
                          order_type=self.order_type,
                          quantity=self.quantity - transact_quantity,
                          agent_id=self.agent_id,
                          time=self.time,
                          )
        self.update_quantity_filled(self.quantity - transact_quantity)
        return new_order

    def __eq__(self, other: 'Order') -> bool:
        return self.order_id == other.order_id

    def __gt__(self, other: 'Order') -> bool:
        if self.order_type == -1 and other.order_type == -1:
            return (self.price, self.time) < (other.price, other.time)
        elif self.order_type == 1 and other.order_type == 1:
            return (self.price, -self.time) > (other.price, -other.time)
        # I don't think these are needed
        elif self.order_type == -1:
            return self.price < other.price
        elif self.order_type == 1:
            return self.price > other.price


@dataclass
class MatchedOrder:
    price: Price
    time: int
    order: Order
