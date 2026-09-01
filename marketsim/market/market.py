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
from marketsim.plot.simple_plot import plot_order_book
from marketsim.input import config
from marketsim.market.price import Price
from marketsim.fourheap.fourheap import FourHeap

if TYPE_CHECKING:
    from marketsim.fourheap import Order, MatchedOrder
    from marketsim.agent import Agent


class Market:
    def __init__(self, fundamental: Fundamental, time_steps: int, reference_price: Price |None = None, name: str|None=None,
                 market_type: str = "discrete"):
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
        self.fundamental = fundamental

        self.event_queue = EventQueue()
        self.end_time = time_steps
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
            self.orders_by_agent_type.setdefault(agent.group, {"Count_buy":0, "Volume_buy":0, "Count_sell":0, "Volume_sell":0})
            self.trades_by_agent_type.setdefault(agent.group,
                                                 {"Count_buy": 0, "Volume_buy": 0, "Count_sell": 0, "Volume_sell": 0})
            self.trades_by_agent_type_ext.setdefault(agent.group,
                                                 {"Count_buy": {"arrived":0, "waited":0}, "Volume_buy": {"arrived":0, "waited":0}
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
            self.matched_orders_hashed[inner_order.order_id] = {"price":inner_order.price,
                                                                "quantity":inner_order.quantity,
                                                                "order_type":inner_order.order_type
                                                                }
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

    def step(self, current_time: int) -> list[MatchedOrder]:
        # TODO Need to figure out how to handle ties for price and time - AK: maybe fractal time?
        self.logger.info(f"Starting step for time tick: {str(current_time)}")
        # rolling the traded_prices first:
        if current_time-1 in self.traded_prices and current_time not in self.traded_prices:
            yesterday = self.traded_prices[current_time-1]
            self.traded_prices[current_time] = {"Open": yesterday["Close"],
                                                "Low": yesterday["Close"],
                                                "High": yesterday["Close"],
                                                "Close": yesterday["Close"],
                                                "Volume": 0, }

        orders = self.event_queue.get_activities(current_time=current_time)
        self.buy_init_volume, self.sell_init_volume = 0, 0
        newly_matched_orders = []
        self.bid_ask_history.setdefault(current_time, [self.order_book.buy_unmatched.peek(), self.order_book.sell_unmatched.peek()])
        self.logger.info(f"Current spread is: {self.order_book.buy_unmatched.peek()} {self.order_book.sell_unmatched.peek()}")
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
        newly_matched_orders += self.clear_market(current_time=current_time)

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

    def record_trade(self, matched_order: MatchedOrder) -> None:
        self.last_traded_price = matched_order.price

        # record for plots and summary:
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
        # record for each agent:
        agent_id = matched_order.order.agent_id
        self.agents[agent_id].record_trade(matched_order=matched_order)
        # record it by type:
        if matched_order.order.order_type == 1:
            self.trades_by_agent_type[self.agents[matched_order.order.agent_id].group]["Count_buy"] += 1
            self.trades_by_agent_type[self.agents[matched_order.order.agent_id].group]["Volume_buy"] += matched_order.order.quantity
            # and the ext version - filling the waited/arrived value - why not use a pandas DF?
            self.trades_by_agent_type_ext[self.agents[matched_order.order.agent_id].group]["Count_buy"][matched_order.order.executed_mode] += 1
            self.trades_by_agent_type_ext[self.agents[matched_order.order.agent_id].group]["Volume_buy"][matched_order.order.executed_mode] += matched_order.order.quantity
        elif matched_order.order.order_type == -1:
            self.trades_by_agent_type[self.agents[matched_order.order.agent_id].group]["Count_sell"] += 1
            self.trades_by_agent_type[self.agents[matched_order.order.agent_id].group]["Volume_sell"] += matched_order.order.quantity
            self.trades_by_agent_type_ext[self.agents[matched_order.order.agent_id].group]["Count_sell"][matched_order.order.executed_mode] += 1
            self.trades_by_agent_type_ext[self.agents[matched_order.order.agent_id].group]["Volume_sell"][matched_order.order.executed_mode] += matched_order.order.quantity
        else:
            raise ValueError(f"Unknown order type {matched_order.order.order_type}")

    def __str__(self) -> str:
        return f"Market_{self.asset_id}"

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
            output_file=f"{config.output_dir}/LOB/LOB_{self.asset_id}_{current_time}.png",
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
