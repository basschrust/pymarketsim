from marketsim.agent.washtrading_pool import WashTradingAgent
from marketsim.simulator.simulator import Simulator

sim = Simulator(
    num_background_zi_agents=2,
    sim_time=10,#1_000,
    num_assets=1,
    lam=0.5,           # default arrival intensity for background agents
    mean=100.0,        # long-run fundamental value
    r=0.02,             # mean-reversion strength
    shock_var=10.0,    # volatility of fundamental shocks
    q_max=10,          # max order size for background agents (AK: max position)
    pv_var=10,         # variance of private values
)

# add the WashTradingAgents here:
market = sim.markets[0]
buying_agent = WashTradingAgent(market=market, q_max=10, pool_id=0, manipulation_side='BUY', manipulation_type='PULL_UP')
selling_agent = WashTradingAgent(market=market, q_max=10, pool_id=0, manipulation_side='SELL', manipulation_type='PULL_UP')
sim.add_agents([buying_agent, selling_agent])

sim.run()

# Inspect market statistics once the run completes
market = sim.markets[0]
mid_prices = market.get_midprices()
matched_orders = market.matched_orders
