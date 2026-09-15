import random
from marketsim.agent.agent import Agent
from marketsim.market.market import Market, Price
from marketsim.fourheap.order import Order
from marketsim.private_values.private_values import PrivateValues
from marketsim.fourheap.constants import BUY, SELL
from marketsim.utils.id_generator import id_generator


class SpoofingAgent(Agent):
    def __init__(self, market: Market, q_max: int, pv_var: float, order_size:int, spoofing_size: int,
                 normalizers: dict, spoofing_times: list[int]|None):
        super().__init__(market=market)
        self.group = "SP"
        self.agent_id = id_generator.next()
        self.market = market
        if pv_var is not None:
            self.pv = pv_var
        else:
            self.pv = PrivateValues(q_max, float(pv_var))
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

        if spoofing_times is None:
            self.spoofing_times = [50, 1300, 2345, 3709]
        else:
            self.spoofing_times = spoofing_times

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
        orders = []
        if current_time in self.spoofing_times:
            self.market.withdraw_all(agent_id=self.get_id())
            spoof_side = random.choice([-1, 1])

            # TODO - calculate them - we can inspect LOB (just like WTs)!
            if spoof_side == -1:
                regular_order_price = self.market.last_traded_price + Price(0.4)
                spoofing_order_price = self.market.last_traded_price - Price(0.01)
            else:
                regular_order_price = self.market.last_traded_price - Price(0.4)
                spoofing_order_price = self.market.last_traded_price + Price(0.01)
                # TODO: make those prices configurable

            # TODO: we can make it a little more sophisticated! lol
            # 1. toss sides
            # 2. take action in some special time ticks (high or low volume? or defined tick numer)
            # 3. add valid_until field to the Order class and cancel each order which reaches this value
            # (cancel at the beginning of the step)

            # Regular order.
            # self.logger.info(f"Normalizers fundamental: {self.normalizers['fundamental'].__class__}")
            regular_order = Order(
                price=Price(float(regular_order_price)), # * float(self.normalizers["fundamental"])),
                quantity=self.order_size,
                agent_id=self.get_id(),
                time=current_time,
                order_type=-1*spoof_side,
                asset_id=self.market.asset_id,
            )
            orders.append(regular_order)

            # Spoofing Order
            # TODO: we have to cancel the order very quickly, before it is executed!
            # TODO: but the traders to be tricked are HBL - so they have to trade some reasonable volume!
            spoofing_order = Order(
                price=Price(float(spoofing_order_price)), # * float(self.normalizers["fundamental"])),
                quantity=self.spoofing_size,
                agent_id=self.get_id(),
                time=current_time,
                order_type=spoof_side,
                asset_id=self.market.asset_id,
                valid_until=current_time+2, # TODO: check, maybe +1 would be enough
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



