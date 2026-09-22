import pandas as pd

from .price import Price
from .market import Market
from marketsim.input import config
from marketsim.fourheap import Order
from .valuation_libs.BlackScholes import BSCall
from marketsim.plot.candle import plot_candlestick_derivative

class Option(Market):
    def __init__(self, time_steps: int, underlying: Market, market_type: str = "continuous",
                 name: str| None = None, strike: Price= Price(100), expiration: str = "1Y"
                 , option_side: str= "CALL", option_type: str= "European") -> None:
        super().__init__(time_steps=time_steps, name=name,  market_type=market_type)
        self.underlying = underlying
        self.strike = strike
        self.expiration = 1  if expiration == '1Y' else expiration # TODO: prepare mapper for this
            # so that we can give relative time or precise dates or just take it from option series
        self.option_side = option_side
        self.option_type = option_type
        self.r = 0 # the risk-free financing rate
        self.volatility = 0.157  # annualized volatility of the underlying security
        # TODO: reference price should be theoretical - what about calculating this and then calling super()?

        theoretical_price = 10 # self.get_theoretical_price() # TODO: None here?

        # structures to be extended
        self.traded_prices = {0: {"Open": self.last_traded_price,
                                  "Low": self.last_traded_price,
                                  "High": self.last_traded_price,
                                  "Close": self.last_traded_price,
                                  "Theoretical": theoretical_price,
                                  "Volume": 0, }}

    def calculate_greeks(self):
        pass

    def get_theoretical_price(self) -> Price:
        # TODO: is current_time needed as parameter?
        # returns theoretical price of the option, using BS formula
        call_option = BSCall(self.underlying.last_traded_price, self.strike, self.r, self.volatility, self.expiration, 0.0)
        # TODO: this gives us the option price along with its Greeks :)
        return call_option["price"]

    def fill_theoretical_price(self):
        for t, price_row in self.traded_prices.items():
            if "Theoretical" in price_row:
                pass
            else:
                call_option = BSCall(self.underlying.last_traded_price, self.strike, self.r, self.volatility,
                                     self.expiration, 0.0)
                price_row["Theoretical"] = call_option.get("price", 100)



    def plot_history(self):
        # ensure that theoretical will be plotted, too:
        self.fill_theoretical_price()

        traded_prices_float = {t: {v: float(price_item) for v, price_item in item.items()}
                               for t, item in self.traded_prices.items()}
        df_candlestick = pd.DataFrame.from_dict(traded_prices_float,
                                                orient="index"
                                                )
        df_candlestick.index.name = "time"
        self.logger.info(df_candlestick.head())

        candlestick_filename = f"{config.output_dir}/candlestick_{str(self)}.png"
        plot_candlestick_derivative(df=df_candlestick, output_file=candlestick_filename, title=self.name)

