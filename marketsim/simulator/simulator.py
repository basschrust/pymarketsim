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
                 sim_time: int,
                 lam: float = 0.1,
                 mean: float = 100.0,
                 r: float = .6,
                 shock_var=10,
                 markets: dict = {},
                 lob_plot_interval: int = 10,
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

            for group_name, agent_group in m_conf["agent_groups"].items():
                for i in range(agent_group["number"]):
                    # let's make it in case/ series of ifs to avoid security breach (if used the class name as code directly)
                    # ZI agents:
                    if agent_group["agent_class"] == "ZIAgentNotInformed":
                            agent = ZIAgentNotInformed(markets=[market], **agent_group["config"])
                            self.add_agents([agent])

                    # Noise agents:
                    if agent_group["agent_class"] == "NoiseAgent":
                        agent = NoiseAgent(markets=[market], **agent_group["config"])
                        self.add_agents([agent])

                    # MMs:
                    if agent_group["agent_class"] == "MMZOHAgent":
                        agent = MMZOHAgent(markets=[market], **agent_group["config"])
                        self.add_agents([agent])

                    # HBL (Heuristic Belief)
                    if agent_group["agent_class"] == "HBLAgent":
                        agent = HBLAgent(markets=[market], **agent_group["config"])
                        self.add_agents([agent])

                    # spoofers: (to trick HBL Agents)
                    if agent_group["agent_class"] == "SpoofingAgent":
                        agent = SpoofingAgent(markets=[market], **agent_group["config"])
                        self.add_agents([agent])

                    # washtrading agents (tricking MMs)
                    if agent_group["agent_class"] == "WashTradingAgent":
                        agent = WashTradingAgent(markets=[market], group_name=group_name, **agent_group["config"])
                        self.add_agents([agent])
                        # those will need the relationship...

                    # momentum
                    if agent_group["agent_class"] == "MomentumAgent":
                        agent = MomentumAgent(markets=[market], **agent_group["config"])
                        self.add_agents([agent])

                    ########## Derivatives agents, complicated ones :)  ###############

                    ## MM, simple delta hedger
                    if agent_group["agent_class"] == "OptionMMZOHAgent":
                        agent = OptionMMZOHAgent(option_markets=[market], underlying_market=market.underlying,
                                                 **agent_group["config"])
                        self.add_agents([agent])

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

        return

    ######################### __init__ ends here   ###################

    def add_agents(self, agents: list[Agent]) -> None:
        for agent in agents:
            self.logger.info(f"Adding agent {str(agent)} to the simulation")
            self.agents[agent.get_id()] = agent

            for asset_id, market in agent.markets.items(): # TODO: this will serve the multimarket agents soon
                market.add_agents([agent]) # TODO: check performance

    def step(self) -> None:
        # TODO: changing the architecture - fist agents, the markets
        for agent_id, agent in self.agents.items():
            agent.take_action(current_time=self.current_time)  #
            # now agents decide which markets to enter on their own
            #market.logger.info(f'Agent {agent.agent_id} is entering the market {str(market)} and makes orders {orders}')
            #market.add_orders(orders)  # moved to agent


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
            market.logger.info(f"Market {str(market)}:")
            # fundamental_val = Price(market.get_final_fundamental())
            # market.logger.info(f"Final fundamental: {fundamental_val}")
            market.logger.info(f"Orders matched: {len(market.matched_orders)}")
            market.logger.info(f"Last traded price: {market.last_traded_price}")
            # values_by_fundamental = {}
            values_by_last_traded_price = {}
            for agent_id in market.agents:
                agent = market.agents[agent_id]
                # values_by_fundamental[agent_id] = Price(agent.get_pos_value()) + agent.position * fundamental_val + agent.cash
                values_by_last_traded_price[agent_id] = agent.position[market.asset_id] * market.last_traded_price + agent.cash
            # TODO: put the results in separate, simple (CSV) files
            # market.logger.info(f'At the end of the simulation we get valuations by fundamental: {values_by_fundamental}')
            positions_sum = 0
            cash_sum = 0
            values_by_last_trade_sum = 0
            for i, agent in market.agents.items():
                market.logger.info(f"Agent {str(agent)}: \tposition: {agent.position}  \tcash: {agent.cash} "
                      # f"\tvalue(by fund.): {values_by_fundamental[i]} \t"
                                   f"value(by last trade): {values_by_last_traded_price[i]}")
                positions_sum += agent.position[market.asset_id]
                cash_sum += agent.cash
                values_by_last_trade_sum += market.last_traded_price * agent.position[market.asset_id]
            market.logger.info(f"Positions sum: {positions_sum}")
            market.logger.info(f"Cash sum: {cash_sum}")
            market.logger.info(f"Sum of values by last traded price: {values_by_last_trade_sum}")
            # market.logger.info(f"Sum of values by fundamental: {sum(values_by_fundamental.values())}")
            market.logger.info(f"Midprices: {market.get_midprices()}")
            market.logger.info(f"Traded prices {market.traded_prices}")

            # valuations by agent:
            for agent_key, agent in market.agents.items():
                value_history = agent.position_value_history
                position_history = agent.position_history
                market.logger.info(f"\nAgent {str(agent_key)} value history\n: {value_history}")
                market.logger.info(f"\nAgent {str(agent_key)} position history\n: {position_history}")

                # plot it
                agent_file = f"{config.output_dir}/{str(market)}/by_agents/{str(market)}_agent_{str(agent)}.png"

                plot_agent_history(
                    position_history=position_history[market.asset_id], # TODO: yet only his first market
                    value_history=value_history,
                    output_file=agent_file,
                )

            # plot the security values history:
            market.plot_history()

            # plotting by type:
            plot_by_type(market.orders_by_agent_type, output_file=f"{config.output_dir}/{str(market)}/orders_by_type_{str(market)}.png", title=f"Orders by type in {market.name}")
            plot_by_type(market.trades_by_agent_type,
                                output_file=f"{config.output_dir}/{str(market)}/trades_by_type_{str(market)}.png", title=f"Trades by type in {market.name}")
            plot_by_type(market.trades_by_agent_type_ext,
                         output_file=f"{config.output_dir}/{str(market)}/trades_by_type_ext_{str(market)}.png",
                         title=f"Trades by extended type in {market.name}", mode="extended")
            plot_bid_ask(market.bid_ask_history,
                         output_file=f"{config.output_dir}/{str(market)}/bid_ask_history_{str(market)}.png",
                         title=f"Bid ask spread history {str(market)}")
            #calculate and plot realized volatility:
            window = 50
            volatility = market.calculate_realized_volatility(window=window)
            plot_realized_volatility(volatility=volatility,
                                     output_file=f"{config.output_dir}/{str(market)}/realized_volatility_{str(market)}.png",
                                     title=f"Realized volatility {str(market)} with window {window}")

            # plot the history of trading between agent groups:
            market.plot_trade_stats()

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
