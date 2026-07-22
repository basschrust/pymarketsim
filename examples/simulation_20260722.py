import inspect

from marketsim.agent.washtrading_pool import WashTradingAgent
from marketsim.simulator.simulator import Simulator
from marketsim.market.market import Price
from marketsim.input.config import CONFIG


def kwargs_for(func, config):
    params = inspect.signature(func).parameters
    return {k: v for k, v in config.items() if k in params}


sim = Simulator(**kwargs_for(Simulator, CONFIG))
    # **CONFIG
    # num_background_zi_agents_informed=0,
    # num_background_zi_agents_not_informed=40,
    # sim_time=30,#1_000,
    # num_assets=1,
    # lam=0.5,           # default arrival intensity for background agents
    # mean=100.0,        # long-run fundamental value
    # r=0.02,             # mean-reversion strength
    # shock_var=10.0,    # volatility of fundamental shocks
    # q_max=10,          # max order size for background agents (AK: max position)
    # pv_var=10,         # variance of private values
# )

# add the WashTradingAgents here:
market = sim.markets[0]
# buying_agent = WashTradingAgent(market=market, q_max=10, pool_id=0, manipulation_side='BUY', manipulation_type='PULL_UP')
# selling_agent = WashTradingAgent(market=market, q_max=10, pool_id=0, manipulation_side='SELL', manipulation_type='PULL_UP')
# sim.add_agents([buying_agent, selling_agent])

sim.run()

# Inspect market statistics once the run completes
market = sim.markets[0]
mid_prices = market.get_midprices()
matched_orders = market.matched_orders
