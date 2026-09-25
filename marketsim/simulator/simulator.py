import pandas as pd
from loguru import logger
from typing import TYPE_CHECKING

from marketsim.loggers.basic import terminal

from marketsim.fundamental.mean_reverting import GaussianMeanReverting
from marketsim.fundamental.lazy_mean_reverting import LazyGaussianMeanReverting
from marketsim.utils.id_generator import id_generator
from marketsim.plot.simple_plot import (simple_plot, plot_agent_history, plot_by_type, plot_bid_ask
, plot_realized_volatility, plot_volume_transfers)
from marketsim.plot.candle import plot_candlestick
from marketsim.input import config
from marketsim.market import Price, Market, Option
from marketsim.agent import Agent, WashTradingAgent, MomentumAgent, SpoofingAgent, NoiseAgent
from marketsim.agent import ZIAgentInformed, ZIAgentNotInformed, MMZOHAgent, HBLAgent, OptionMMZOHAgent
from marketsim.agent.washtrading import WashTradingPool


class Simulator:
    def __init__(self,
                 *,
                 sim_time: int,
                 lam: float = 0.1,
                 mean: float = 100.0,
                 r: float = .6,
                 shock_var=10,
                 markets: dict = {},
                 lob_plot_interval: int = 10,
                 agents: dict|None=None,
                 ):
        self.logger = logger.bind()
        self.logger.info("Initializing simulation with parameters in market_structure.yaml ...")

        self.sim_time = sim_time
        self.lam = lam # lambda (activity factor)
        self.mean = mean
        self.r = r
        self.shock_var = shock_var # change probability of fundamental (market consensus) value

        self.current_time = 0 # TODO: needed in Market, here probably not?
        self.markets = {} # [] # each market serves single security, keys are asset_ids
        self.market_map = {} # { yaml_id: asset_id }

        self.agents = {} # boys are back in town! agents here instead of markets, as one agents serves many markets
        self.lob_plot_interval = lob_plot_interval
        self.last_progress = -1
        self.bar_length = 40

        for m_key, m_conf in markets.items():
            # TODO: do we need this fundamental at all?
            fundamental = GaussianMeanReverting(mean=self.mean, final_time=self.sim_time, r=self.r,
                                                shock_var=self.shock_var)

            # TODO: how to handle derivatives here?
            instrument_class = m_conf.get("instrument_class", "stock")
            if instrument_class == "option":
                # let's rock with first option here!
                # terminal.write(str(m_conf))
                # terminal.write(str(self.markets))
                underlying = self.markets.get(self.market_map.get(m_conf.get("derivatives_config").get("underlying")))
                market = Option(market_type=m_conf.get("market_type"), name=m_conf.get("name"),
                               derivatives_config=m_conf.get("derivatives_config")
                                , underlying=underlying)
            elif instrument_class == "stock":
                market = Market(market_type=m_conf.get("market_type"), name=m_conf.get("name"))
            else:
                raise ValueError(f"Unknown instrument_class: {instrument_class}")

            self.market_map[m_key] = market.asset_id
            self.markets[market.asset_id] = market

            for group_name, agent_group in m_conf.get("agent_groups", {}).items():
                self.add_agent_group(agent_group=agent_group, markets=[market], group_name=group_name)

            # TODO: resolve agent dependencies
            for relationship in m_conf.get("agent_dependencies", []):
                if relationship["type"] == "wash_trading_pool":
                    # terminal.write(f"Adding washtrading relationship:")
                    buy_pool = relationship["buy_pool"]
                    sell_pool = relationship["sell_pool"]

                    # TODO: now set the pool hook in the agents...
                    # check all agents with group name "buy_pool" or "sell_pool" ?
                    buy_pool_agents = []
                    sell_pool_agents = []
                    for agent in market.agents.values():
                        if agent.group_name == buy_pool:
                            # terminal.write(f"\nFound buy agent {agent.agent_id}")
                            buy_pool_agents.append(agent)
                        elif agent.group_name == sell_pool:
                            # terminal.write(f"\nFound sell agent {agent.agent_id}")
                            sell_pool_agents.append(agent)

                    pool = WashTradingPool(buy_pool=buy_pool_agents, sell_pool=sell_pool_agents)
                    for agent in buy_pool_agents:
                        # terminal.write(f"\nsetting pool for agent  {agent.agent_id}...")
                        agent.set_wt_pool(wt_pool=pool)
                    for agent in sell_pool_agents:
                        # terminal.write(f"\nsetting pool for agent  {agent.agent_id}...")
                        agent.set_wt_pool(wt_pool=pool)

        for a_key, agent_gr_def in agents.items():
            self.create_agents(agent_group=agent_gr_def, group_name=a_key)
        return

    ######################### __init__ ends here   ###################
    #
    # def create_defined_agent(self, *, agent_def: dict, markets: list[Market], number: int = 1) -> None:
    #     for i in range(number):


    def add_agent_group(self, *, agent_group:dict, markets: list[Market], group_name: str) -> None:
        for i in range(agent_group["number"]):
            # let's make it in case/ series of ifs to avoid security breach (if used the class name as code directly)
            # ZI agents:
            if agent_group["agent_class"] == "ZIAgentNotInformed":
                agent = ZIAgentNotInformed(markets=markets, **agent_group["config"])
                self.add_agents([agent])

            # Noise agents:
            if agent_group["agent_class"] == "NoiseAgent":
                agent = NoiseAgent(markets=markets, **agent_group["config"])
                self.add_agents([agent])

            # MMs:
            if agent_group["agent_class"] == "MMZOHAgent":
                agent = MMZOHAgent(markets=markets, **agent_group["config"])
                self.add_agents([agent])

            # HBL (Heuristic Belief)
            if agent_group["agent_class"] == "HBLAgent":
                agent = HBLAgent(markets=markets, **agent_group["config"])
                self.add_agents([agent])

            # spoofers: (to trick HBL Agents)
            if agent_group["agent_class"] == "SpoofingAgent":
                agent = SpoofingAgent(markets=markets, **agent_group["config"])
                self.add_agents([agent])

            # washtrading agents (tricking MMs)
            if agent_group["agent_class"] == "WashTradingAgent":
                agent = WashTradingAgent(markets=markets, group_name=group_name, **agent_group["config"])
                self.add_agents([agent])
                # those will need the relationship...

            # momentum
            if agent_group["agent_class"] == "MomentumAgent":
                agent = MomentumAgent(markets=markets, **agent_group["config"])
                self.add_agents([agent])

            ########## Derivatives agents, complicated ones :)  ###############

            ## MM, simple delta hedger
            if agent_group["agent_class"] == "OptionMMZOHAgent":
                # TODO - what with underlying?
                agent = OptionMMZOHAgent(markets=markets, market_map=self.market_map, #underlying_market=market.underlying,
                                         **agent_group["config"])
                self.add_agents([agent])

    def create_agents(self, *, agent_group: dict, group_name: str) -> None:
        # processing the agents defined at the end of yaml
        if agent_group.get("markets", "ALL") == "ALL":
            markets = list(self.markets.values())
        else:
            markets = [self.markets[self.market_map[k]] for k in agent_group["markets"]]

        self.add_agent_group(agent_group=agent_group, markets=markets, group_name=group_name)

    def add_agents(self, agents: list[Agent]) -> None:
        for agent in agents:
            self.logger.info(f"Adding agent {str(agent)} to the simulation")
            self.agents[agent.get_id()] = agent

            for asset_id, market in agent.markets.items(): # TODO: this will serve the multimarket agents soon
                market.add_agents([agent]) # TODO: check performance

    def step(self) -> None:
        # TODO: changing the architecture - first agents, then markets
        for agent_id, agent in self.agents.items():
            agent.take_action(current_time=self.current_time)  #
            # now agents decide which markets to enter on their own

        for market_key, market in self.markets.items():

            # plot the LOB
            if self.current_time > 0 and self.current_time % self.lob_plot_interval == 0:
                market.plot_lob(self.current_time)

            market.logger.info(f"Starting orders execution, matched queues should be empty here: {len(market.order_book.buy_matched.heap)}"
                  f" {len(market.order_book.sell_matched.heap)}")
            new_orders_matched = market.step(current_time=self.current_time)

            market.logger.info(f"Starting to clear out orders.")
            # initiate market prices instance for the case of no trades: - moved to market.step

            for matched_order in new_orders_matched:
                market.logger.info(f"Matched order {str(matched_order)}")
                market.record_trade(matched_order=matched_order)
            market.logger.info(f'After clearing the market the last traded price is: {market.last_traded_price}')
            market.logger.info(f'And the spread: {market.order_book.buy_unmatched.peek()} {market.order_book.sell_unmatched.peek()}')

        # update value of each agent after each market has been cleared:
        for agent_id, agent in self.agents.items():
            agent.record_valuation(current_time=self.current_time) #, price=market.last_traded_price)

        self.current_time += 1


    def end_sim(self) -> None:
        """ End the simulation and print summary """
        self.logger.info(f"\n\nSimulation ended. time: {self.current_time}")
        self.last_progress = -1
        self.show_progress_bar(step=0, total=len(self.markets), step_name="Markets")
        market_steps = 0
        for market_key, market in self.markets.items():
            market.show_summary()

            self.show_progress_bar(step=market_steps, total=len(self.markets), step_name="Markets")
            market_steps += 1

    def show_progress_bar(self, step: int, total: int | None = None, step_name: str = "Steps") -> None:
        if total is None:
            total = self.sim_time
        progress = (step + 1) / total
        percentage = int(progress * 100)

        if percentage != self.last_progress:
            filled = int(self.bar_length * progress)
            bar = "█" * filled + "░" * (self.bar_length - filled)

            terminal.write(
                f"\r|{bar}| {percentage:3d}%   {step_name} completed: {step + 1}/{total}"
            )
            terminal.flush()

            self.last_progress = percentage


    def run(self) -> None:
        terminal.write("\nStarting simulation...\n")

        for step in range(self.sim_time):
            self.logger.info(f"Simulation step start: {step}.", end='')
            self.step()
            self.show_progress_bar(step)

        terminal.write("\nSimulation complete.")
        terminal.write("\nPreparing summary...\n")
        self.end_sim()
        terminal.write("\nSummary complete.")
