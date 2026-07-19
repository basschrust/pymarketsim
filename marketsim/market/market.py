from marketsim.event.event_queue import EventQueue
from marketsim.fourheap.fourheap import FourHeap, Order
from marketsim.fundamental.fundamental_abc import Fundamental
from marketsim.fourheap import constants


class Market:
    def __init__(self, fundamental: Fundamental, time_steps: int, reference_price: float= None):
        self.order_book = FourHeap()
        self.matched_orders = []
        self.fundamental = fundamental
        self.last_traded_price = reference_price if reference_price else 100
        self.event_queue = EventQueue()
        self.end_time = time_steps


    def get_fundamental_value(self, current_time):
        #t = self.get_time()
        #return self.fundamental.get_value_at(t)
        return self.fundamental.get_value_at(current_time)

    def get_final_fundamental(self):
        return self.fundamental.get_final_fundamental()

    def withdraw_all(self, agent_id: int) -> None:
        self.order_book.withdraw_all(agent_id)

    def clear_market(self, current_time: int) -> list[Order]:
        new_orders = self.order_book.market_clear(current_time=current_time) # self.get_time())
        self.matched_orders += new_orders
        return new_orders

    def add_orders(self, orders):
        for order in orders:
            self.event_queue.schedule_activity(order)

    def get_time(self):
        return self.event_queue.get_current_time()

    def get_info(self):
        return self.fundamental.get_info()

    def step(self, current_time) -> list[Order]:
        # TODO Need to figure out how to handle ties for price and time
        #orders = self.event_queue.step()
        orders = self.event_queue.get_activities(current_time=current_time)
        self.buy_init_volume, self.sell_init_volume = 0, 0
        for order in orders:
            if order.quantity <= 0:
                continue
            self.order_book.insert(order)
        new_orders = self.clear_market(current_time=current_time)

        # Compute midprices.
        self.order_book.update_midprice()
        return new_orders

    def get_midprices(self) ->list:
        return self.order_book.midprices

    def reset(self, fundamental: Fundamental) -> None:
        print("Resetting market...")
        self.order_book = FourHeap()
        self.matched_orders = []
        self.event_queue = EventQueue()
        self.fundamental = fundamental  # AK: this implies some market consensus on the fundamental value
                            # it may make sense for the ZI agents group, but probably should be kept out of here
                            # and belong to the groups
