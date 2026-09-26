from __future__ import annotations

import inspect
from collections.abc import Callable
from typing import TYPE_CHECKING
import random
import numpy as np

from marketsim.input.config import CONFIG
from marketsim.loggers.basic import StreamToLogger
from marketsim.plot.simple_plot import simple_plot
from marketsim.simulator import Simulator

if TYPE_CHECKING:
    from marketsim.market import Price

random.seed(CONFIG["seed"])
np.random.seed(CONFIG["seed"])


def kwargs_for(func: Callable, config: dict) -> dict:
    params = inspect.signature(func).parameters
    return {k: v for k, v in config.items() if k in params}


sim = Simulator(**kwargs_for(Simulator, CONFIG))

sim.run()
