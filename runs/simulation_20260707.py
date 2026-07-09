from marketsim.simulator.simulator import Simulator

sim = Simulator(
    num_background_zi_agents=50,
    sim_time=100,#1_000,
    num_assets=1,
    lam=0.5,           # arrival intensity for background agents
    mean=100.0,        # long-run fundamental value
    r=0.2,             # mean-reversion strength
    shock_var=10.0,    # volatility of fundamental shocks
    q_max=10,          # max order size for background agents (AK: max position)
    pv_var=10,         # variance of private values
)

sim.run()

# Inspect market statistics once the run completes
market = sim.markets[0]
mid_prices = market.get_midprices()
matched_orders = market.matched_orders
