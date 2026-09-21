
from .price import Price
from .market import Market

class Option(Market):
    def __init__(self, time_steps: int, underlying: Market, market_type: str | None = "continuous", name: str| None = None, strike: Price= Price(100), expiration: str = "1Y"
                 , option_side: str= "CALL", option_type: str= "European") -> None:
        super().__init__(time_steps=time_steps, name=name,  market_type=market_type)
        self.underlying = underlying
        self.strike = strike
        self.expiration = expiration
        self.option_side = option_side
        self.option_type = option_type

    def calculate_greeks(self):
        pass

