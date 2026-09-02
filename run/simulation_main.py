from __future__ import annotations

import inspect
from typing import TYPE_CHECKING

from marketsim.input.config import CONFIG
from marketsim.loggers.basic import StreamToLogger
from marketsim.plot.simple_plot import simple_plot
from marketsim.simulator import Simulator

if TYPE_CHECKING:
    from marketsim.market import Price


def kwargs_for(func, config):
    params = inspect.signature(func).parameters
    return {k: v for k, v in config.items() if k in params}


sim = Simulator(**kwargs_for(Simulator, CONFIG))

sim.run()

# Inspect market statistics once the run completes
market = sim.markets[0]
mid_prices = market.get_midprices()
matched_orders = market.matched_orders
