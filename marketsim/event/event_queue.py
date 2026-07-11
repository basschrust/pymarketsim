import random
from collections import defaultdict
from typing import List

from marketsim.fourheap.order import Order


class EventQueue:
    def __init__(self, rand_seed: int = None):
        self.rand = random.Random(rand_seed)
        self.scheduled_activities = defaultdict(list)
        self.current_time = 0

    def schedule_activity(self, order: Order):
        t = order.time

        self.scheduled_activities[t].append(order)

    def step(self) -> List[Order]:
        random.shuffle(self.scheduled_activities[self.current_time])
        self.current_time += 1 # TODO: AK: isn't it redundant? step in market, step in queue.
                               # that's why matched order has time t+1, while placed order t
                                # without it nothing happens on the market, we have to align it somehow

        return self.scheduled_activities[self.current_time - 1]

    def get_current_time(self):
        return self.current_time

    def set_time(self, t):
        self.current_time = t
