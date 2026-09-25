import pandas as pd

from .price import Price
from .market import Market
from marketsim.input import config
from marketsim.fourheap import Order, MatchedOrder
from .valuation_libs.BlackScholes import BSCall, BSPut
from marketsim.plot.candle import plot_candlestick_derivative

class Option(Market):
    def __init__(self, derivatives_config: dict, underlying: Market,
                 market_type: str = "continuous",
                 name: str| None = None) -> None:
                 # strike: Price=Price(100), expiration: str = "1Y"
                 # , option_side: str= "CALL", option_type: str= "European") -> None:

        self.instrument_class = "option"
        self.underlying = underlying
        self.strike = derivatives_config["strike"]
        self.expiration = 1.0  if derivatives_config["expiration"] == '1Y' else derivatives_config["expiration"] # TODO: prepare mapper for this
            # so that we can give relative time or precise dates or just take it from option series
        self.option_side = derivatives_config["option_side"]
        self.option_type = derivatives_config["option_type"]
        self.r = 0 # the risk-free financing rate
        self.volatility = 0.157  # annualized volatility of the underlying security
        # TODO: reference price should be theoretical - what about calculating this and then calling super()?
        theoretical_price = self.get_theoretical_price()
        super().__init__(name=name, market_type=market_type, reference_price=Price(theoretical_price)
                         , instrument_class=self.instrument_class)

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
        if self.option_side == "CALL":
            call_option = BSCall(S=self.underlying.last_traded_price, K=self.strike,
                                 r=self.r, volatility=self.volatility, Time=self.expiration, d=0.0)
            # TODO: this gives us the option price along with its Greeks :)
            return call_option["price"]
        elif self.option_side == "PUT":
            put_option = BSPut(S=self.underlying.last_traded_price, K=self.strike,
                                 r=self.r, volatility=self.volatility, Time=self.expiration, d=0.0)
            # TODO: this gives us the option price along with its Greeks :)
            return put_option["price"]
        else:
            ValueError(f"Unknown option side: {self.option_side}")

    def fill_theoretical_price(self):
        for t, price_row in self.traded_prices.items():
            if "Theoretical" in price_row:
                pass
            else:
                if self.option_side == "CALL":
                    call_option = BSCall(S=price_row.get("Close"), K=self.strike, r=self.r,
                                         volatility=self.volatility,
                                         Time=self.expiration, d=0.0)
                    price_row["Theoretical"] = call_option.get("price", 100)
                elif self.option_side == "PUT":
                    put_option = BSPut(S=price_row.get("Close"), K=self.strike, r=self.r,
                                         volatility=self.volatility,
                                         Time=self.expiration, d=0.0)
                    price_row["Theoretical"] = put_option.get("price", 100)

    def roll_traded_prices(self, current_time:int) -> None:
        yesterday = self.traded_prices[current_time - 1]
        self.traded_prices[current_time] = {"Open": yesterday["Close"],
                                            "Low": yesterday["Close"],
                                            "High": yesterday["Close"],
                                            "Close": yesterday["Close"],
                                            "Volume": 0,
                                            "Theoretical": self.get_theoretical_price(), }

    def record_volume_and_price(self, matched_order: MatchedOrder) -> None:
        # overriden in derivatives to include theoretical
        current_time = matched_order.time
        price = matched_order.price
        volume = matched_order.order.quantity
        if current_time in self.traded_prices:
            # update data
            if price > self.traded_prices[current_time]["High"]:
                self.traded_prices[current_time]["High"] = price
            elif price < self.traded_prices[current_time]["Low"]:
                self.traded_prices[current_time]["Low"] = price
            old_volume = self.traded_prices[current_time]["Volume"]
            self.traded_prices[current_time]["Volume"] = volume + old_volume
            self.traded_prices[current_time]["Close"] = price
            self.traded_prices[current_time]["Theoretical"] = self.get_theoretical_price()
        else:
            # enter as first day in this time tick
            self.traded_prices[current_time] = { "Open": price,
                                                 "Low": price,
                                                 "High": price,
                                                 "Close": price,
                                                 "Volume": volume,
                                                 "Theoretical": self.get_theoretical_price(),}

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

