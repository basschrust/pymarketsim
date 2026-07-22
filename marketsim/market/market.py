from marketsim.market.price import Price
from marketsim.event.event_queue import EventQueue
from marketsim.fourheap.fourheap import FourHeap, Order, MatchedOrder
from marketsim.fundamental.fundamental_abc import Fundamental
from marketsim.fourheap import constants


class Market:
    def __init__(self, fundamental: Fundamental, time_steps: int, reference_price: Price= Price(100),
                 market_type: str = "discrete"):
        self.order_book = FourHeap()
        self.matched_orders = [] # stores a list of all trades from the beginning of trading to the end of simulation
        self.fundamental = fundamental
        self.last_traded_price = reference_price
        self.event_queue = EventQueue()
        self.end_time = time_steps
        self.market_type = market_type # "discrete" or "continuous"


    def get_fundamental_value(self, current_time: int) -> float:
        return self.fundamental.get_value_at(current_time)

    def get_final_fundamental(self) -> float:
        return self.fundamental.get_final_fundamental()

    def withdraw_all(self, agent_id: int) -> None:
        self.order_book.withdraw_all(agent_id=agent_id)

    def clear_market(self, current_time: int) -> list[MatchedOrder]:
        newly_matched_orders = self.order_book.market_clear(current_time=current_time)
        self.matched_orders += newly_matched_orders
        return newly_matched_orders

    def add_orders(self, orders: list[Order]) -> None:
        for order in orders:
            self.event_queue.schedule_activity(order)

    def get_time(self):
        raise # to make sure it is not used
        return self.event_queue.get_current_time()

    def get_info(self):
        return self.fundamental.get_info()

    def step(self, current_time: int) -> list[MatchedOrder]:
        # TODO Need to figure out how to handle ties for price and time
        orders = self.event_queue.get_activities(current_time=current_time)
        self.buy_init_volume, self.sell_init_volume = 0, 0
        newly_matched_orders = []
        for order in orders:
            if order.quantity <= 0:
                continue
            self.order_book.insert(order)
            # if we are in continuous mode we should clear the market here, after entering each order
            #let's see what happens ...
            if self.market_type == "continuous":
                newly_matched_orders += self.clear_market(current_time=current_time)
        newly_matched_orders += self.clear_market(current_time=current_time)

        # Compute midprices. AK - in continuous mode it may need a change
        self.order_book.update_midprice(current_time=current_time)
        return newly_matched_orders

    def get_midprices(self) -> list:
        return self.order_book.midprices

    def reset(self, fundamental: Fundamental) -> None:
        print("Resetting market...")
        self.order_book = FourHeap()
        self.matched_orders = []
        self.event_queue = EventQueue()
        self.fundamental = fundamental  # AK: this implies some market consensus on the fundamental value
                            # it may make sense for the ZI agents group, but probably should be kept out of here
                            # and belong to the groups
