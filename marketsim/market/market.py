from __future__ import annotations

import pandas as pd
from collections import defaultdict
from itertools import accumulate
from loguru import logger
from typing import TYPE_CHECKING
import math

from marketsim.event import EventQueue
from marketsim.fundamental.fundamental_abc import Fundamental
from marketsim.utils.id_generator import id_generator
from marketsim.plot.simple_plot import (plot_order_book, plot_volume_transfers, plot_cash_transfers
    , plot_realized_volatility, plot_agent_history, plot_by_type, plot_bid_ask)
from marketsim.plot.candle import plot_candlestick
from marketsim.input import config
from marketsim.market.price import Price
from marketsim.fourheap.fourheap import FourHeap

if TYPE_CHECKING:
    from marketsim.fourheap import Order, MatchedOrder
    from marketsim.agent import Agent


class Market:
    def __init__(self, reference_price: Price |None = None, name: str|None=None,
                 market_type: str = "discrete", instrument_class: str = "stock"):
        self.instrument_class = instrument_class
        self.last_traded_price = reference_price if reference_price is not None else Price(100)
        self.asset_id = id_generator.next()
        self.order_book = FourHeap(plus_one=True, market=self)
        self.matched_orders = [] # stores a list of all trades from the beginning of trading to the end of simulation
        self.matched_orders_hashed = {} # {order_id: { "price": price, "quantity":quantity }}
        self.traded_prices = {0:{"Open": self.last_traded_price,
                                                "Low": self.last_traded_price,
                                                "High": self.last_traded_price,
                                                "Close": self.last_traded_price,
                                                "Volume": 0, }}
        self.bid_ask_history = {}
        self.realized_volatility = {0:0}
        self.orders_by_agent_type = {}
        self.trades_by_agent_type = {}
        self.trades_by_agent_type_ext = {}
        # by groups - including counterparty groups:
        self.trade_history_by_groups = {}
        self.agent_groups = set()
        # and let's use the power of DataFrames:
        self.trade_stats = {}
        self.trade_stats_df = pd.DataFrame()

        # TODO: check if this fundamental (externally provided value) is needed here
        # self.fundamental = fundamental

        self.event_queue = EventQueue()
        # self.end_time = time_steps
        self.market_type = market_type # "discrete" or "continuous" # TODO: what if two phased? or more phased :)
        self.agents = {}
        self.name = name
        logger.add(
            f"{config.output_dir}/market_{self.asset_id}.log",
            format="{elapsed} | {message}",
            level="DEBUG" if config.debug_logging else "INFO",
            filter=lambda record, market_id=self.asset_id:
            record["extra"].get("market_id") == market_id,
        )
        self.logger = logger.bind(market_id=self.asset_id)

    def add_agents(self, agents: list[Agent] | None) -> None:
        for agent in agents:
            self.logger.info(f"Adding agent {str(agent)} to market {str(self)}")
            self.agents[agent.get_id()] = agent
            self.agent_groups.add(agent.group)
            self.orders_by_agent_type.setdefault(agent.group, {"Count_buy":0, "Volume_buy":0, "Count_sell":0, "Volume_sell":0})
            self.trades_by_agent_type.setdefault(agent.group,
                                                 {"Count_buy": 0, "Volume_buy": 0, "Count_sell": 0, "Volume_sell": 0})
            self.trades_by_agent_type_ext.setdefault(agent.group,
                                                 {"Count_buy": {"arrived":0, "waited":0}, "Volume_buy": {"arrived":0, "waited":0}
                                                     , "Count_sell": {"arrived":0, "waited":0}, "Volume_sell": {"arrived":0, "waited":0}})
            # this one is tricky as requires n-square combination
            # TODO: but also with already existing groups!
            # and then by time...
        for g1 in self.agent_groups:
            for g2 in self.agent_groups:
                self.trade_history_by_groups.setdefault(g1, {}).setdefault(g2,{"Count_buy": {"arrived":0, "waited":0}, "Volume_buy": {"arrived":0, "waited":0}
                                                     , "Count_sell": {"arrived":0, "waited":0}, "Volume_sell": {"arrived":0, "waited":0}})


    def get_fundamental_value(self, current_time: int) -> float:
        return self.fundamental.get_value_at(current_time)

    def get_final_fundamental(self) -> float:
        return self.fundamental.get_final_fundamental()

    def withdraw_all(self, agent_id: int) -> None:
        self.order_book.withdraw_all(agent_id=agent_id)

    def clear_market(self, current_time: int) -> list[MatchedOrder]:
        newly_matched_orders = self.order_book.market_clear(current_time=current_time, trading_phase="continuous")
        self.matched_orders += newly_matched_orders
        for matched_order in newly_matched_orders:
            inner_order = matched_order.order
            self.matched_orders_hashed[inner_order.order_id] =  matched_order
                                                         # TODO: it requires change in the HBL agents implementation
            # the limit from the order is needed, not the executed price
        return newly_matched_orders

    def add_orders(self, orders: list[Order]) -> None:
        for order in orders:
            self.event_queue.schedule_activity(order)
            if order.order_type == 1:
                self.orders_by_agent_type[self.agents[order.agent_id].group]["Count_buy"] += 1
                self.orders_by_agent_type[self.agents[order.agent_id].group]["Volume_buy"] += order.quantity
            elif order.order_type == -1:
                self.orders_by_agent_type[self.agents[order.agent_id].group]["Count_sell"] += 1
                self.orders_by_agent_type[self.agents[order.agent_id].group]["Volume_sell"] += order.quantity

    def get_time(self):
        raise # to make sure it is not used
        return self.event_queue.get_current_time()

    def get_info(self):
        return self.fundamental.get_info()

    def cancel_outdated_orders(self, current_time: int):
        # TODO: go to event_queue and delete the ones that should be cancelled due to time
        self.order_book.cancel_outdated_orders(current_time=current_time)

    def roll_traded_prices(self, current_time:int) -> None:
        yesterday = self.traded_prices[current_time - 1]
        self.traded_prices[current_time] = {"Open": yesterday["Close"],
                                            "Low": yesterday["Close"],
                                            "High": yesterday["Close"],
                                            "Close": yesterday["Close"],
                                            "Volume": 0, }

    def step(self, current_time: int) -> list[MatchedOrder]:
        # TODO Need to figure out how to handle ties for price and time - AK: maybe fractal time?
        self.logger.info(f"Starting step for time tick: {str(current_time)}")
        # first:cancel orders that are no longer valid
        self.cancel_outdated_orders(current_time=current_time)

        # second: rolling the traded_prices
        if current_time-1 in self.traded_prices and current_time not in self.traded_prices:
            self.roll_traded_prices(current_time=current_time)

            for g1 in self.agent_groups:
                for g2 in self.agent_groups:
                    key = (current_time, g1, g2)
                    self.trade_stats[key] = {"Count_buy": 0,
                                         "Volume_buy": 0,
                                         "Cash_buy": 0,
                                         "Count_sell": 0,
                                         "Volume_sell": 0,
                                         "Cash_sell": 0,
                                         }

        # taking the orders from queue to LOB:
        orders = self.event_queue.get_activities(current_time=current_time)
        self.buy_init_volume, self.sell_init_volume = 0, 0
        newly_matched_orders = []
        self.bid_ask_history.setdefault(current_time, [self.order_book.buy_unmatched.peek(), self.order_book.sell_unmatched.peek()])
        self.logger.info(f"Starting step {current_time}. Current spread is: {self.order_book.buy_unmatched.peek()} {self.order_book.sell_unmatched.peek()}")
        self.logger.info(
            f"Defined by orders: buy: {self.order_book.buy_unmatched.heap[0][1] if not self.order_book.buy_unmatched.is_empty() else '<None>'}"
            f", sell: {self.order_book.sell_unmatched.heap[0][1] if not self.order_book.sell_unmatched.is_empty() else '<None>'}")
        self.logger.info(
            f"With volumes: buy: {self.order_book.buy_unmatched.peek_order()}"
            f", sell: {self.order_book.sell_unmatched.peek_order()}")
        # plot the order book state here - first just print it:
        self.logger.info(f"The LOB buy orders: {self.order_book.buy_unmatched.heap}")
        self.logger.info(f"The LOB sell orders: {self.order_book.sell_unmatched.heap}")

        for order in orders:
            if order.quantity <= 0:
                continue
            self.logger.info(f"Inserting order: {order}")
            self.order_book.insert(order)
            # if we are in continuous mode we should clear the market here, after entering each order
            #let's see what happens ...
            if self.market_type == "continuous":
                newly_matched_orders += self.clear_market(current_time=current_time)

        # after all orders have been inserted into LOB the cleraing procedure should start in the "fixing" phase
        newly_matched_orders_2 = self.clear_market(current_time=current_time)
        newly_matched_orders += newly_matched_orders_2
        if newly_matched_orders_2:
            #raise # currently we're in continuous only - so here no order should be matched
            # but it reaches this point :/
            self.logger.info(f"Should not reach this point, matched: {newly_matched_orders}")

        # Compute midprices. AK - in continuous mode it may need a change
        self.order_book.update_midprice(current_time=current_time)
        return newly_matched_orders

    def get_midprices(self) -> list:
        return self.order_book.midprices

    def reset(self, fundamental: Fundamental) -> None:
        self.logger.info("Resetting market...")
        self.order_book = FourHeap()
        self.matched_orders = []
        self.event_queue = EventQueue()
        self.fundamental = fundamental  # AK: this implies some market consensus on the fundamental value
                            # it may make sense for the ZI agents group, but probably should be kept out of here
                            # and belong to the groups

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
        else:
            # enter as first day in this time tick
            self.traded_prices[current_time] = { "Open": price,
                                                 "Low": price,
                                                 "High": price,
                                                 "Close": price,
                                                 "Volume": volume,}


    def record_trade(self, matched_order: MatchedOrder) -> None:
        self.last_traded_price = matched_order.price

        # record for plots and summary:
        current_time = matched_order.time
        self.record_volume_and_price(matched_order=matched_order)

        # record for each agent:
        agent_id = matched_order.order.agent_id
        self.agents[agent_id].record_trade(matched_order=matched_order)
        # record it by type:
        cp_agent = self.matched_orders_hashed[matched_order.order.matched_with].order.agent_id
        cp_group = self.agents[cp_agent].group
        key = (current_time, self.agents[matched_order.order.agent_id].group, cp_group)

        if matched_order.order.order_type == 1:
            self.trades_by_agent_type[self.agents[matched_order.order.agent_id].group]["Count_buy"] += 1
            self.trades_by_agent_type[self.agents[matched_order.order.agent_id].group]["Volume_buy"] += matched_order.order.quantity
            # and the ext version - filling the waited/arrived value - why not use a pandas DF?
            self.trades_by_agent_type_ext[self.agents[matched_order.order.agent_id].group]["Count_buy"][matched_order.order.executed_mode] += 1
            self.trades_by_agent_type_ext[self.agents[matched_order.order.agent_id].group]["Volume_buy"][matched_order.order.executed_mode] += matched_order.order.quantity
            # and with information about counterparty group:
            self.trade_history_by_groups[self.agents[matched_order.order.agent_id].group][cp_group]["Count_buy"][matched_order.order.executed_mode] += 1
            self.trade_history_by_groups[self.agents[matched_order.order.agent_id].group][cp_group]["Volume_buy"][matched_order.order.executed_mode] += matched_order.order.quantity

            # use the power of Pandas DFs (later in conversion:) ):
            if key not in self.trade_stats:
                self.trade_stats[key] = {"Count_buy": 1,
                                         "Volume_buy": matched_order.order.quantity,
                                         "Cash_buy": matched_order.order.quantity * matched_order.price,
                                         "Count_sell": 0,
                                         "Volume_sell": 0,
                                         "Cash_sell": 0
                                         }
            else:
                self.trade_stats[key]["Count_buy"] += 1
                self.trade_stats[key]["Volume_buy"] += matched_order.order.quantity
                self.trade_stats[key]["Cash_buy"] += matched_order.order.quantity * matched_order.price

        elif matched_order.order.order_type == -1:
            self.trades_by_agent_type[self.agents[matched_order.order.agent_id].group]["Count_sell"] += 1
            self.trades_by_agent_type[self.agents[matched_order.order.agent_id].group]["Volume_sell"] += matched_order.order.quantity
            self.trades_by_agent_type_ext[self.agents[matched_order.order.agent_id].group]["Count_sell"][matched_order.order.executed_mode] += 1
            self.trades_by_agent_type_ext[self.agents[matched_order.order.agent_id].group]["Volume_sell"][matched_order.order.executed_mode] += matched_order.order.quantity
            # split by ccp:
            self.trade_history_by_groups[self.agents[matched_order.order.agent_id].group][cp_group]["Count_sell"][
                matched_order.order.executed_mode] += 1
            self.trade_history_by_groups[self.agents[matched_order.order.agent_id].group][cp_group]["Volume_sell"][
                matched_order.order.executed_mode] += matched_order.order.quantity

            # use the power of Pandas DFs (later in conversion:) ):
            if key not in self.trade_stats:
                self.trade_stats[key] = {"Count_buy": 0,
                                         "Volume_buy": 0,
                                         "Cash_buy": 0,
                                         "Count_sell": 1,
                                         "Volume_sell": matched_order.order.quantity,
                                         "Cash_sell": matched_order.order.quantity * matched_order.price,
                                         }
            else:
                self.trade_stats[key]["Count_sell"] += 1
                self.trade_stats[key]["Volume_sell"] += matched_order.order.quantity
                self.trade_stats[key]["Cash_sell"] += matched_order.order.quantity * matched_order.price
        else:
            raise ValueError(f"Unknown order type {matched_order.order.order_type}")

    def __str__(self) -> str:
        return f"Market_{self.asset_id}"

    ## plotting and supporting functions     #######################

    def aggregate_order_queue(self, order_queue: dict, reverse: bool=False, cumulative: bool=False):
        aggregated = defaultdict(int)

        for price, order_id in order_queue:
            buy_order = self.order_book.buy_unmatched.order_dict.get(order_id)
            sell_order = self.order_book.sell_unmatched.order_dict.get(order_id)

            quantity = (
                    (buy_order.quantity if buy_order is not None else 0)
                    + (sell_order.quantity if sell_order is not None else 0)
            )
            aggregated[abs(price)] += quantity

        items = sorted(aggregated.items(), reverse=reverse)

        if cumulative:
            volumes = list(accumulate(volume for _, volume in items))
            items = [(price, volume) for (price, _), volume in zip(items, volumes)]

        return dict(items)

    def plot_lob(self, current_time:int):
        bids = self.aggregate_order_queue(order_queue=self.order_book.buy_unmatched.heap)
        asks = self.aggregate_order_queue(order_queue=self.order_book.sell_unmatched.heap)

        self.logger.info(f"Bids: {bids}") # TODO: it sums IDs here, not volumes!
        self.logger.info(f"Asks: {asks}")

        plot_order_book(
            bids=bids,
            asks=asks,
            output_file=f"{config.output_dir}/{str(self)}/LOB/LOB_{self.asset_id}_{current_time}.png",
            title=f"Order book at {current_time}"
        )

    def calculate_realized_volatility(
            self,
            window: int = 20,
    ) -> dict:
        """
        Calculate rolling realized volatility from closing prices.

        Returns:
            {time_tick: realized_volatility}
        """
        times = sorted(self.traded_prices)

        # Close price for each tick
        closes = {
            t: float(self.traded_prices[t]["Close"])
            for t in times
        }

        # Log returns
        returns = {}
        previous_price = None

        for t in times:
            price = closes[t]
            if (
                    previous_price is not None
                    and previous_price > 0
                    and price > 0
            ):
                returns[t] = math.log(price / previous_price)
            previous_price = price

        # Rolling realized volatility
        volatility = {}
        return_times = sorted(returns)

        for i, t in enumerate(return_times):
            window_returns = list(
                returns.values()
            )[max(0, i - window + 1): i + 1]

            volatility[t] = math.sqrt(
                sum(r * r for r in window_returns)
            )

        return volatility

    def plot_trade_stats(self):
        self.trade_stats_df = pd.DataFrame(
            [
                {
                    "timeTick": timeTick,
                    "agentGroup": agentGroup,
                    "cpGroup": cpGroup,
                    **values,
                }
                for (timeTick, agentGroup, cpGroup), values in self.trade_stats.items()
            ]
        )

        self.logger.info(f"Volume transfers: {self.trade_stats_df.head(30)}")
        plot_volume_transfers(self.trade_stats_df, output_file_tpl=f"{config.output_dir}/{str(self)}/Transfers_vol_{str(self)}_")

        # TODO: plot cash transfers
        plot_cash_transfers(self.trade_stats_df, output_file_tpl=f"{config.output_dir}/{str(self)}/Transfers_cash_{str(self)}_")

    def plot_history(self):
        traded_prices_float = {t: {v: float(price_item) for v, price_item in item.items()}
                               for t, item in self.traded_prices.items()}
        df_candlestick = pd.DataFrame.from_dict(traded_prices_float,
                                                orient="index"
                                                )
        df_candlestick.index.name = "time"
        self.logger.info(df_candlestick.head())

        candlestick_filename = f"{config.output_dir}/candlestick_{str(self)}.png"
        plot_candlestick(df=df_candlestick, output_file=candlestick_filename, title=self.name)

    def show_summary(self):
        self.logger.info(f"\n\nMarket {str(self)} summary:")
        # fundamental_val = Price(market.get_final_fundamental())
        # market.logger.info(f"Final fundamental: {fundamental_val}")
        self.logger.info(f"Orders matched: {len(self.matched_orders)}")
        self.logger.info(f"Last traded price: {self.last_traded_price}")
        # values_by_fundamental = {}
        values_by_last_traded_price = {}
        for agent_id in self.agents:
            agent = self.agents[agent_id]
            # values_by_fundamental[agent_id] = Price(agent.get_pos_value()) + agent.position * fundamental_val + agent.cash
            # TODO: dimensions!
            values_by_last_traded_price[agent_id] = agent.position[
                                                        self.asset_id] * self.last_traded_price + agent.cash
        # TODO: put the results in separate, simple (CSV) files
        # market.logger.info(f'At the end of the simulation we get valuations by fundamental: {values_by_fundamental}')
        positions_sum = 0
        cash_sum = 0
        values_by_last_trade_sum = 0
        for i, agent in self.agents.items():
            self.logger.info(f"Agent {str(agent)}: \tposition: {agent.position}  \tcash: {agent.cash} "
                               # f"\tvalue(by fund.): {values_by_fundamental[i]} \t"
                               f"value(by last trade): {values_by_last_traded_price[i]}")
            # TODO: dimensions!
            positions_sum += agent.position[self.asset_id]
            cash_sum += agent.cash
            values_by_last_trade_sum += self.last_traded_price * agent.position[self.asset_id]
        self.logger.info(f"Positions sum: {positions_sum}")
        self.logger.info(f"Cash sum: {cash_sum}")
        self.logger.info(f"Sum of values by last traded price: {values_by_last_trade_sum}")
        # market.logger.info(f"Sum of values by fundamental: {sum(values_by_fundamental.values())}")
        self.logger.info(f"Midprices: {self.get_midprices()}")
        self.logger.info(f"Traded prices {self.traded_prices}")

        # valuations by agent:
        for agent_key, agent in self.agents.items():
            value_history = agent.position_value_history
            position_history = agent.position_history
            self.logger.info(f"\nAgent {str(agent_key)} value history\n: {value_history}")
            self.logger.info(f"\nAgent {str(agent_key)} position history\n: {position_history}")

            # plot it
            agent_file = f"{config.output_dir}/{str(self)}/by_agents/{str(self)}_agent_{str(agent)}.png"

            plot_agent_history(
                # TODO: dimensions in position_history have changed!
                position_history=position_history[self.asset_id],  # TODO: yet only his first market
                value_history=value_history,
                output_file=agent_file,
            )

        # plot the security values history:
        self.plot_history()

        # plotting by type:
        plot_by_type(self.orders_by_agent_type,
                     output_file=f"{config.output_dir}/{str(self)}/orders_by_type_{str(self)}.png",
                     title=f"Orders by type in {market.name}")
        plot_by_type(self.trades_by_agent_type,
                     output_file=f"{config.output_dir}/{str(self)}/trades_by_type_{str(self)}.png",
                     title=f"Trades by type in {self.name}")
        plot_by_type(self.trades_by_agent_type_ext,
                     output_file=f"{config.output_dir}/{str(self)}/trades_by_type_ext_{str(self)}.png",
                     title=f"Trades by extended type in {self.name}", mode="extended")
        plot_bid_ask(self.bid_ask_history,
                     output_file=f"{config.output_dir}/{str(self)}/bid_ask_history_{str(self)}.png",
                     title=f"Bid ask spread history {str(self)}")
        # calculate and plot realized volatility:
        window = 50
        volatility = self.calculate_realized_volatility(window=window)
        plot_realized_volatility(volatility=volatility,
                                 output_file=f"{config.output_dir}/{str(self)}/realized_volatility_{str(self)}.png",
                                 title=f"Realized volatility {str(self)} with window {window}")

        # plot the history of trading between agent groups:
        self.plot_trade_stats()
