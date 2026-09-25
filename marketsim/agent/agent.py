from __future__ import annotations

from abc import ABC, abstractmethod
import copy
import math
from typing import List
from dataclasses import dataclass, field
import traceback
from typing import TYPE_CHECKING
from collections import defaultdict

from marketsim.utils.id_generator import id_generator
from marketsim.loggers.basic import terminal
from marketsim.market.price import Price

if TYPE_CHECKING:
    from marketsim.fourheap import Order, MatchedOrder
    from marketsim.market import Market


def validate_update(quantity: int, cash: Price) -> None:
    if not math.isfinite(cash):
        raise ValueError(f"cash must be finite (not NaN or ±inf) as here: {cash}")

    if quantity <= 0:
        if cash < 0:
            raise ValueError("Cash cannot be negative if quantity is negative!")

    if quantity >= 0:
        if cash > 0:
            raise ValueError("Cash cannot be positive if quantity is positive!")


class Agent(ABC):
    # An agent is an investor operating on single market (investing in single security against their cash)

    def __init__(self, markets: list[Market], group_name: str | None = None):
        # self.market = market
        self.agent_id = id_generator.next()
        #self.markets = [self.market]
        self.markets = { market.asset_id: market for market in markets } # converting to dict
        self.group_name = group_name

        self.trade_history = {}  # dict of lists/dicts {time: [trades over that day, volume bought, volume sold]}
        self.position_value_history = {} # {time: position_value}
        # self.position = 0
        self.position = { m_id: 0 for m_id  in self.markets }
        # self.position_history = {0: 0}  # {time: number_of_shares} # at the end of tick
        self.position_history = defaultdict(dict)
        self.position_history[0] = { m_id:0  for m_id  in self.markets }  # {time: {asset_id: number_of_shares}}
        # at the end of tick
        self._cash = Price(0)
        self.logger = markets[0].logger

    @property
    def cash(self):
        return self._cash

    @cash.setter
    def cash(self, value):
        # print(f"Agent {id(self)} cash: {self._cash} -> {value}")
        # traceback.print_stack(limit=2)
        self._cash = value

    @abstractmethod
    def get_id(self) -> int:
        return self.agent_id

    @abstractmethod
    def take_action(self, current_time: int) -> None:
        # for each of its markets put the orders of the agent
        pass

    @abstractmethod
    def get_pos_value(self) -> float:
        pass

    def update_position(self, quantity: int, cash: Price, asset_id: int) -> None:
        validate_update(quantity=quantity, cash=cash)
        # self.logger.info(f"Update position, agent: {self.agent_id}, old: {self.position}")
        if asset_id not in self.position:
            terminal.write(f"Position:  {self.position}. {asset_id} not in position")
        self.position[asset_id] += quantity
        # self.logger.info(f"New: {self.position}")
        self.cash += cash

    def reset(self) -> None:
        self.position = { m_id: 0 for m_id  in self.markets}
        self.cash = Price(0)

    def is_market_maker(self) -> bool:
        raise # this is utterly deprecated
        return False

    def record_valuation(self, current_time: int) -> None:
        # saving value of agents portfolio
        # TODO: copy value, not reference!
        # terminal.write(f"Position: {self.position}")
        self.position_history[current_time] = copy.deepcopy(self.position)

        # valuation by last trade:
        self.position_value_history[current_time] = self.cash
        for asset_id, market in self.markets.items():
            self.position_value_history[current_time] += int(self.position[asset_id]) * market.last_traded_price

    def record_trade(self, matched_order: MatchedOrder) -> None:
        quantity = matched_order.order.order_type * matched_order.order.quantity
        cash = - Price(matched_order.price * matched_order.order.quantity * matched_order.order.order_type)
        # print(f"Updating cash: {cash}")
        self.update_position(quantity=quantity, cash=cash, asset_id=matched_order.order.asset_id)
        self.position_history[matched_order.time][matched_order.order.asset_id] = (
                self.position_history.get(matched_order.time, {}).get(matched_order.order.asset_id, 0) + quantity)

        if matched_order.time in self.trade_history:
            # just add info
            old = self.trade_history.get(matched_order.time, {}).get(matched_order.order.asset_id, {})
            if old:
                self.trade_history[matched_order.time][matched_order.order.asset_id] = {"trades": old["trades"]+1,
                                                               "volume": old["volume"] + abs(matched_order.order.quantity),}
            else:
                # first trade on this security on this date:
                self.trade_history[matched_order.time][matched_order.order.asset_id] = {"trades": 1, "volume": abs(matched_order.order.quantity),
                                                }
        else:
            # first trade this day
            self.trade_history[matched_order.time] = { matched_order.order.asset_id: {"trades": 1, "volume": abs(matched_order.order.quantity),
                                                    } }# side, volume bought/sold, ...

        # TODO: record also with what kind of agent the capital was exchanged with.
        # and record it also per group...
        # TODO: structure like: self.trade_history_by_groups =
        #  {"MM":{ timeTick1: { volumeBought: , volumeSold: , cashBalance: }, timeTick2: {} } }
        # TODO: reconcile it at the end

