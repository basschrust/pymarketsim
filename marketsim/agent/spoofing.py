import random
from marketsim.agent.agent import Agent
from marketsim.market.market import Market, Price
from marketsim.fourheap.order import Order
from marketsim.private_values.private_values import PrivateValues
from marketsim.fourheap.constants import BUY, SELL
from marketsim.utils.id_generator import id_generator


class SpoofingAgent(Agent):
    def __init__(self, market: Market, q_max: int, pv_var: float, order_size:int, spoofing_size: int, normalizers: dict):
        super().__init__(market=market)
        self.group = "SP"
        self.agent_id = id_generator.next()
        self.market = market
        self.pv = PrivateValues(q_max, pv_var)
        self.position = 0
        self.spoofing_size = spoofing_size
        self.order_size = order_size
        self.cash = 0
        self.last_value = 0 # value at last time step (liquidate all inventory)
        self.normalizers = normalizers # A dictionary {"fundamental": float, "invt": float, "cash": float}
        self.spoofing_size = spoofing_size
        self.regular_order_size = order_size

        self.q_max = q_max
        self.pv_var = pv_var

    def get_id(self) -> int:
        return self.agent_id

    def estimate_fundamental(self):
        mean, r, T = self.market.get_info()
        t = self.market.get_time()
        val = self.market.get_fundamental_value()

        rho = (1-r)**(T-t)

        estimate = (1-rho) * mean + rho*val
        # print(f'It is time {t} with final time {T} and I observed {val} and my estimate is {rho, estimate}')
        return estimate

    def take_action(self, current_time:int):
        # TODO - calculate them
        regular_order_price = self.market.last_traded_price + Price(0.4)
        spoofing_order_price = self.market.last_traded_price - Price(0.01)

        orders = []
        # Regular order.
        regular_order = Order(
            price=Price(float(regular_order_price) * self.normalizers["fundamental"]),
            quantity=self.order_size,
            agent_id=self.get_id(),
            time=current_time,
            order_type=SELL,
            asset_id=self.market.asset_id,
        )
        orders.append(regular_order)

        # Spoofing Order
        spoofing_order = Order(
            price=Price(float(spoofing_order_price) * self.normalizers["fundamental"]),
            quantity=self.spoofing_size,
            agent_id=self.get_id(),
            time=current_time,
            order_type=BUY,
            asset_id=self.market.asset_id,
        )
        orders.append(spoofing_order)

        return orders

    def __str__(self):
        return f'SP{self.agent_id}'

    def get_pos_value(self) -> float:
        return self.pv.value_at_position(self.position)

    def reset(self):
        self.pv = PrivateValues(self.q_max, self.pv_var)
        self.position = 0
        self.cash = 0
        self.last_value = 0



