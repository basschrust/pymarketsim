
from .price import Price
from .market import Market
from marketsim.fourheap import Order
from .valuation_libs.BlackScholes import BSCall

class Option(Market):
    def __init__(self, time_steps: int, underlying: Market, market_type: str = "continuous", name: str| None = None, strike: Price= Price(100), expiration: str = "1Y"
                 , option_side: str= "CALL", option_type: str= "European") -> None:
        super().__init__(time_steps=time_steps, name=name,  market_type=market_type)
        self.underlying = underlying
        self.strike = strike
        self.expiration = expiration
        self.option_side = option_side
        self.option_type = option_type
        # TODO: reference price should be theoretical - what about calculating this and then calling super()?

    def calculate_greeks(self):
        pass

    def get_theoretical_price(self) -> Price:
        # returns theoretical price of the option, using BS formula
        call_option = BSCall(self.underlying.last_traded_price, self.strike, self.r, self.volatility, self.expiration, 0.0)
        # TODO: this gives us the option price along with its Greeks :)
        return call_option["price"]

