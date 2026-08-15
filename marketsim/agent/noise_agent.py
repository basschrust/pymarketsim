import random
from decimal import Decimal
from marketsim.agent.agent import Agent
from marketsim.market.market import Market
from marketsim.fourheap.order import Order
from marketsim.fourheap.constants import BUY, SELL
from typing import List
import numpy as np
from marketsim.utils.id_generator import id_generator
from marketsim.market.price import Price


class NoiseAgent(Agent):
    """
    Noise agent - aware only of last traded price and his own position (but this also only roughly)
    """
    def __init__(self, market: Market, q_max: int, lam=1.0, mean_volume: float = 5.0, mean_spread: Price = Price(0.2)):
        super().__init__(market=market)
        self.group = "Noise"
        self.agent_id = id_generator.next()
        self.market = market
        self.q_max = q_max # check if doesn't collide with mean_volume
        self.position = 0
        self.cash = 0
        self.lam = lam # activity parameter
        self.mean_volume = mean_volume
        self.mean_spread = mean_spread

    def get_id(self) -> int:
        return self.agent_id

    def estimate_fundamental(self, current_time: int) -> Price:
        raise # should not be used for noise agent

    def take_action(self, current_time: int):
        orders = []
        if random.random() < self.lam:
            # self.market.withdraw_all(agent_id=self.agent_id) # TODO: check the impact on resistance/support
            side = random.choice([BUY, SELL])
            # side chosen randomly and stick to that, but later this agent may place many orders on chosen side
            quantity = np.random.poisson(lam=self.mean_volume) # AK why not volume?
            # quantity = 3 if side == BUY else 5 # just for tests - use prime numbers to check splittings properly
            spread_side = random.choice([-1, 1])
            price = self.market.last_traded_price + spread_side * np.random.poisson(lam=float(self.mean_spread))

            if price > 0:
                order = Order(
                    price=Price(price),
                    quantity=quantity,
                    agent_id=self.agent_id,
                    time=current_time,
                    order_type=side,
                    asset_id=self.market.asset_id,
                )
                orders.append(order)
            else:
                print(f"Order not placed as calculated price was negative: {price}, q: {quantity}")

        return orders


    def __str__(self) -> str:
        return f'Noise_{self.agent_id}'

    def get_pos_value(self) -> Price:
        return self.cash + self.market.last_traded_price * self.position

    def reset(self) -> None:
        self.position = 0
        self.cash = 0

