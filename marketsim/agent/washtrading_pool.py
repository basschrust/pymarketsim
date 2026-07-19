import random
from marketsim.agent.agent import Agent
from marketsim.market.market import Market
from marketsim.fourheap.order import Order
from marketsim.private_values.private_values import PrivateValues
from marketsim.fourheap.constants import BUY, SELL
from typing import List
import numpy as np
from marketsim.utils.id_generator import id_generator


class WashTradingAgent(Agent):
    def __init__(self, market: Market, q_max: int, pool_id: int = 0,
                    manipulation_type: str = 'PULL_UP', # or 'PUSH_DOWN'
                 manipulation_side: str = 'BUY'):
        self.agent_id = id_generator.next()
        self.market = market
        self.q_max = q_max
        self.position = 0
        self.cash = 0
        self.pool_id = pool_id
        self.manipulation_type = manipulation_type
        self.manipulation_side = manipulation_side #'BUY' # or SELL

    def get_id(self) -> int:
        return self.agent_id


    def take_action(self, current_time: int, estimate: float =None):
        # t = self.market.get_time()
        estimate = 100

        price = estimate

        order = Order(
            price=price,
            quantity=1,
            agent_id=self.agent_id,
            time=current_time,
            order_type=1 if self.manipulation_side=='BUY' else -1,
        )

        return [order]

    def update_position(self, q, p):
        self.position += q
        self.cash += p

    def __str__(self):
        return f'WT_{self.manipulation_type}_{self.manipulation_side}_{self.pool_id}_{self.agent_id}'

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



