from decimal import Decimal
from marketsim.agent.agent import Agent
from marketsim.market.market import Market, Price
from marketsim.fourheap.order import Order
from marketsim.fourheap.constants import BUY, SELL
from marketsim.utils.id_generator import id_generator


class MMZOHAgent(Agent):
    ### Market Maker Zero Order Hold Agent -
    # A MM which just takes into account last traded price and sets new order ladder
    # symmetrically on both sides of this last traded price in each rebalance period
    ###
    def __init__(self, *, market: Market, agent_id: int=None, xi: float= 0.1,
                 K: int = 3, omega: float= 0.1, rebalance_period: int=5, volume: int=7, q_max: int=1000):
        super().__init__(market=market)
        self.group = "MMZOH"
        self.agent_id = agent_id if agent_id is not None else id_generator.next()
        self.market = market # could agent serve multiple markets?

        self.position = 0
        self.cash = 0

        self.xi = Decimal(xi) # step of the order ladder
        self.K = K # number of orders in the ladder
        self.omega = Decimal(omega) # bid ask spread between two closest MM quotations
        self.rebalance_period = rebalance_period
        self.volume = volume
        self.q_max = q_max

    def get_id(self) -> int:
        return self.agent_id


    def is_market_maker(self) -> bool:
        return True


    def take_action(self, current_time: int):
        orders = []
        # add orders only in rebalance periods:
        if current_time % self.rebalance_period == 0:
            # AK - clear previous orders (should we?)
            self.logger.info(f"Withdrawing previous orders ()") # how to check number of orders of this agent?
            self.market.withdraw_all(agent_id=self.agent_id)
            # AK - don't withdraw, but also don't blindly add new orders - just ensure they are balanced
            # that's basically the same to just withdraw all and create new, the problem might be with timing
            # - we could loose the slot in the queue of waiting orders

            # Get the best bid and best ask
            best_ask = self.market.order_book.get_best_ask()
            best_bid = self.market.order_book.get_best_bid()

            self.logger.info(f"Best bid {best_bid}, best ask: {best_ask}")

            estimate = self.market.last_traded_price
            self.logger.info(f"Last traded price: {estimate}")
            HALF = Decimal("0.5")
            st = max(estimate + HALF * self.omega, best_bid)
            bt = min(estimate - HALF * self.omega, best_ask)
            self.logger.info(f"Setting basic spread to: {bt}, {st}")
            buy_volume = self.volume
            sell_volume = self.volume
            # TODO: adjust the spread for position rebalancing
            if abs(self.position) > self.q_max/2:
                if self.position > 0:
                    # the MM position is very long - needs to sell, so lower the prices
                    st = st - HALF * self.omega
                    bt = bt - HALF * self.omega
                    if self.position > 3/4 * self.q_max:
                        # if getting close to max we also limit the volume of buy orders:
                        buy_volume = int(buy_volume /2)
                else:
                    # the MM position is very short - has to buy more, raise the prices
                    st = st + HALF * self.omega
                    bt = bt + HALF * self.omega
                    if self.position < -3/4 * self.q_max:
                        sell_volume = int(sell_volume /2)


            for k in range(self.K):
                price_bid = Price(bt - (k + 1) * self.xi)
                if price_bid > 0:
                    orders.append(
                        Order(
                            price=price_bid,
                            quantity=buy_volume, #7,#1, # we ćould raise the quantity in each ladder step...
                            agent_id=self.agent_id,
                            time=current_time,
                            order_type=BUY,
                            asset_id=self.market.asset_id,
                        )
                    )
                    orders.append(
                        Order(
                            price= Price(st + (k + 1)*self.xi),
                            quantity=sell_volume, # 7,#1,
                            agent_id=self.agent_id,
                            time=current_time,
                            order_type=SELL,
                            asset_id=self.market.asset_id,
                        )
                    )

        return orders


    def get_pos_value(self) -> float:
        return 0

    def __str__(self):
        return f'MM_ZOH{self.agent_id}'

