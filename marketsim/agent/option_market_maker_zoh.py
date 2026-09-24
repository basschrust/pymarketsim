from decimal import Decimal

from marketsim.agent.agent import Agent
from marketsim.market import Market, Price, Option
from marketsim.fourheap.order import Order
from marketsim.fourheap.constants import BUY, SELL
from marketsim.utils.id_generator import id_generator
from marketsim.market.valuation_libs.BlackScholes import BSCall, BSPut


class OptionMMZOHAgent(Agent):
    ### Market Maker Zero Order Hold Agent for Options! -
    # A MM which just takes into account last traded price and sets new order ladder
    # symmetrically on both sides of this last traded price in each rebalance period
    ###
    def __init__(self, *, option_markets: list[Option], underlying_market: Market, agent_id: int=None, xi: float= 0.1,
                 K: int = 3, omega: float= 0.1, rebalance_period: int=5, volume: int=7, q_max: int=1000
                 , rebalance_by: str = "time", rebalance_volume: int = 70):
        all_markets = option_markets
        all_markets.append(underlying_market)
        super().__init__(market=option_markets[0]) # TODO: base should accept all the list
        self.group = "OptionsMMZOH"

        #self.market = option_market # could agent serve multiple markets? YES, with Derivatives and underlying!
        self.option_market = option_markets[0]
        # and many derivatives, one underlying
        self.underlying_market = underlying_market
        self.markets[underlying_market.asset_id] = underlying_market

        # self.position = 0 #TODO dict { market_id: position } ?
        # self.position = {x:0 for x in self.markets}
        self.position = {m_id: 0 for m_id, m in self.markets.items()}

        #  TODO: Market Making parameters - per each market:
        self.xi = Decimal(xi) # step of the order ladder
        self.K = K # number of orders in the ladder
        self.omega = Decimal(omega) # bid ask spread between two closest MM quotations
        self.rebalance_period = rebalance_period
        self.rebalance_by = rebalance_by # time or volume or exposure (in derivatives markets!)
        self.rebalance_volume = rebalance_volume # and this differs for derivatives, too!
        self.last_rebalance_time = 0 # on each market!
        self.cum_volume = 0
        self.volume = volume
        self.q_max = q_max


    def get_id(self) -> int:
        return self.agent_id

    def should_rebalance(self, current_time:int) -> bool:
        if current_time == 0:
            return True
        if self.rebalance_by == "time":
            if current_time % self.rebalance_period == 0:
                return True
        elif self.rebalance_by == "volume":
            # in case of low trading volume period rebalance by time anyway:
            if current_time - self.last_rebalance_time >= self.rebalance_period:
                # TODO: prepare a more sophisticated time comparison function
                self.last_rebalance_time = current_time
                self.cum_volume = 0
                return True
            # TODO: make the calculation, but what about methods - own, global, side, cash?
            self.cum_volume += self.market.traded_prices.get(current_time-1, {}).get("Volume", 0)
            if self.cum_volume >= self.rebalance_volume:
                self.last_rebalance_time = current_time
                self.cum_volume = 0
                return True
        return False

    def take_action(self, current_time: int):
        orders = []
        # add orders only in rebalance periods:
        if self.should_rebalance(current_time):
            # AK - clear previous orders (should we?)
            self.logger.info(f"Withdrawing previous orders ()") # how to check number of orders of this agent?
            self.option_market.withdraw_all(agent_id=self.agent_id)
            # AK - don't withdraw, but also don't blindly add new orders - just ensure they are balanced
            # that's basically the same to just withdraw all and create new, the problem might be with timing
            # - we could loose the slot in the queue of waiting orders

            # Get the best bid and best ask
            best_ask = self.option_market.order_book.get_best_ask()
            best_bid = self.option_market.order_book.get_best_bid()

            self.logger.info(f"Best bid {best_bid}, best ask: {best_ask}")

            #estimate = self.market.last_traded_price
            # TODO: get the theoretical price
            estimate = Price(self.option_market.get_theoretical_price())

            self.logger.info(f"Last traded price: {estimate}")
            HALF = Decimal("0.5")
            st = max(estimate + HALF * self.omega, best_bid)
            bt = min(estimate - HALF * self.omega, best_ask)
            self.logger.info(f"Setting basic spread to: {bt}, {st}")
            buy_volume = self.volume
            sell_volume = self.volume
            # TODO: adjust the spread for position rebalancing
            # if abs(self.position) > self.q_max/2:
            #     if self.position > 0:
            #         # the MM position is very long - needs to sell, so move the prices up
            #         st = st + HALF * self.omega
            #         bt = bt + HALF * self.omega
            #         if self.position > 3/4 * self.q_max:
            #             # if getting close to max we also limit the volume of buy orders:
            #             buy_volume = int(buy_volume /2)
            #             if self.position > self.q_max:
            #                 # if we exceeded the q_max then volume should be only symbolic
            #                 buy_volume = 1
            #     else:
            #         # the MM position is very short - has to buy more, lower the prices
            #         st = st - HALF * self.omega
            #         bt = bt - HALF * self.omega
            #         if self.position < -3/4 * self.q_max:
            #             sell_volume = int(sell_volume /2)
            #             if self.position < - self.q_max:
            #                 sell_volume = 1

            self.logger.info(f"Basic spread (option market) adjusted to: {bt}, {st}")

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
                            asset_id=self.option_market.asset_id,
                        )
                    )
                    orders.append(
                        Order(
                            price= Price(st + (k + 1)*self.xi),
                            quantity=sell_volume, # 7,#1,
                            agent_id=self.agent_id,
                            time=current_time,
                            order_type=SELL,
                            asset_id=self.option_market.asset_id,
                        )
                    )

        # return orders
        # adding orders to the option market:
        self.option_market.add_orders(orders)
        # TODO: add orders to the underlying market
        # calculate Greeks
        # delta / gamma hedge
        # either as adjusting MM orders or by paying spread
        greeks = None
        if self.option_market.option_side == "CALL":
            greeks = BSCall(self.underlying_market.last_traded_price, self.option_market.strike,
                        self.option_market.r, self.option_market.volatility,
               self.option_market.expiration, 0.0)
        elif self.option_market.option_side == "PUT":
            greeks = BSPut(self.underlying_market.last_traded_price, self.option_market.strike,
                            self.option_market.r, self.option_market.volatility,
                            self.option_market.expiration, 0.0)

        self.logger.info(f"Greeks: {greeks}")
        self.logger.info(f"Position: {self.position}")
        # simple delta hedge
        delta = greeks.get("delta")
        # check position and align, check minimum difference which leads to rebalance
        delta_pos = delta * self.position.get(self.option_market.asset_id, 0)
        required_adjustment = int(- delta_pos - self.position.get(self.underlying_market.asset_id, 0))
        if required_adjustment >= 1:
            order = Order(price=self.underlying_market.last_traded_price,
                            quantity=required_adjustment,
                            agent_id=self.agent_id,
                            time=current_time,
                            order_type=BUY,
                            asset_id=self.underlying_market.asset_id,
                            valid_until=current_time+10,
                          )
            self.logger.info(f"Adding buy order to underlying market: {order}")
            self.underlying_market.add_orders([order])
        elif required_adjustment <= -1:
            order = Order(price=self.underlying_market.last_traded_price,
                            quantity=abs(required_adjustment),
                            agent_id=self.agent_id,
                            time=current_time,
                            order_type=SELL,
                            asset_id=self.underlying_market.asset_id,
                            valid_until=current_time+10,
                          )
            self.logger.info(f"Adding sell order to underlying market: {order}")
            self.underlying_market.add_orders([order])


    def get_pos_value(self) -> float:
        return 0

    def __str__(self):
        return f'Opt_MM_ZOH{self.agent_id}'

