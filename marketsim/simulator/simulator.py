import pandas as pd
from loguru import logger
from typing import TYPE_CHECKING

from marketsim.fundamental.mean_reverting import GaussianMeanReverting
from marketsim.fundamental.lazy_mean_reverting import LazyGaussianMeanReverting
from marketsim.utils.id_generator import id_generator
from marketsim.plot.simple_plot import simple_plot, plot_agent_history, plot_by_type, plot_bid_ask, plot_realized_volatility
from marketsim.plot.candle import plot_candlestick
from marketsim.input import config
from marketsim.market import Price, Market
from marketsim.agent import Agent, WashTradingAgent, MomentumAgent, SpoofingAgent, NoiseAgent
from marketsim.agent import ZIAgentInformed, ZIAgentNotInformed, MMZOHAgent, HBLAgent


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
        # logger.add(sink=f"{config.output_dir}/main.log",
        #     format="{elapsed} | {message}",
        # )
        self.logger = logger.bind()
        self.logger.info("Initializing simulation with parameters in market_structure.yaml ...")

        self.sim_time = sim_time
        self.lam = lam # lambda (activity factor)
        self.mean = mean
        self.r = r
        self.shock_var = shock_var # change probability of fundamental (market consensus) value

        self.current_time = 0
        self.markets = [] # each market serves single security

        self.agents = {} # but agents are now moved to markets
        self.lob_plot_interval = lob_plot_interval

        for m_key, m_conf in markets.items():
            # TODO: take parameters from market conf
            fundamental = GaussianMeanReverting(mean=self.mean, final_time=self.sim_time, r=self.r,
                                                shock_var=self.shock_var)

            market = Market(fundamental=fundamental, time_steps=self.sim_time, market_type=m_conf["market_type"], name=m_conf.get("name"))

            self.markets.append(market)

            for group_name, agent_group in m_conf["agent_groups"].items():
                for i in range(agent_group["number"]):
                    # let's make it in case/ series of ifs to avoid security breach (if used the class name as code directly)
                    # ZI agents:
                    if agent_group["agent_class"] == "ZIAgentNotInformed":
                            agent = ZIAgentNotInformed(market=market, **agent_group["config"])
                            market.add_agents([agent])

                    # Noise agents:
                    if agent_group["agent_class"] == "NoiseAgent":
                        agent = NoiseAgent(market=market, **agent_group["config"])
                        market.add_agents([agent])

                    # MMs:
                    if agent_group["agent_class"] == "MMZOHAgent":
                        agent = MMZOHAgent(market=market, **agent_group["config"])
                        market.add_agents([agent])

                    # HBL (Heuristic Belief)
                    if agent_group["agent_class"] == "HBLAgent":
                        agent = HBLAgent(market=market, **agent_group["config"])
                        market.add_agents([agent])

                    # spoofers: (to trick HBL Agents)
                    if agent_group["agent_class"] == "SpoofingAgent":
                        agent = SpoofingAgent(market=market, **agent_group["config"])
                        market.add_agents([agent])

                    # washtrading agents (tricking MMs)
                    if agent_group["agent_class"] == "WashTradingAgent":
                        agent = WashTradingAgent(market=market, **agent_group["config"])
                        market.add_agents([agent])

                    # momentum
                    if agent_group["agent_class"] == "MomentumAgent":
                        agent = MomentumAgent(market=market, **agent_group["config"])
                        market.add_agents([agent])

        return

    def step(self) -> None:
        self.logger.info(f'\nIt is time step {self.current_time}')
        for market in self.markets:
            cash_sum = 0
            for agent_id, agent in market.agents.items():
                cash_sum += agent.cash
            market.logger.info(f"Asserting initial cash sum: {cash_sum}")
            assert cash_sum == 0
            for agent_id in market.agents:
                agent = market.agents[agent_id]
                #if not agent.is_market_maker():
                #    market.withdraw_all(agent_id) # AK: well, the market maker should not withdraw the orders
                                # so moving this to take_action? # the agents take care of it by themselves
                # TODO: but now when agents withdraw their orders at the order defined in market structure
                # TODO: then this may lead to wrong signals as each of them should first see the LOB (!!!)
                orders = agent.take_action(current_time=self.current_time) # but there should be different actions
                            # in different markets, solved: agents are defined inside a single market
                market.logger.info(f'Agent {agent.agent_id} is entering the market {str(market)} and makes orders {orders}')
                market.add_orders(orders)
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
            cash_sum = 0
            for agent_id, agent in market.agents.items():
                cash_sum += agent.cash
            market.logger.info(f"Asserting cash sum: {cash_sum}")
            assert cash_sum == 0
            market.logger.info(f'After clearing the market the last traded price is: {market.last_traded_price}')
            market.logger.info(f'And the spread: {market.order_book.buy_unmatched.peek()} {market.order_book.sell_unmatched.peek()}')
            # update value of each agent in each market:
            for k, agent in market.agents.items():
                agent.record_valuation(current_time=self.current_time, price=market.last_traded_price)

        self.current_time += 1


    def end_sim(self) -> None:
        """ End the simulation and print summary """
        self.logger.info(f"\n\nSimulation ended. time: {self.current_time}")
        for market in self.markets:
            market.logger.info(f"Market {str(market)}:")
            fundamental_val = Price(market.get_final_fundamental())
            market.logger.info(f"Final fundamental: {fundamental_val}")
            market.logger.info(f"Orders matched: {len(market.matched_orders)}")
            market.logger.info(f"Last traded price: {market.last_traded_price}")
            values_by_fundamental = {}
            values_by_last_traded_price = {}
            for agent_id in market.agents:
                agent = market.agents[agent_id]
                values_by_fundamental[agent_id] = Price(agent.get_pos_value()) + agent.position * fundamental_val + agent.cash
                values_by_last_traded_price[agent_id] = agent.position * market.last_traded_price + agent.cash
            market.logger.info(f'At the end of the simulation we get valuations by fundamental: {values_by_fundamental}')
            positions_sum = 0
            cash_sum = 0
            values_by_last_trade_sum = 0
            for i, agent in market.agents.items():
                market.logger.info(f"Agent {str(agent)}: \tposition: {agent.position}  \tcash: {agent.cash} "
                      f"\tvalue(by fund.): {values_by_fundamental[i]} \tvalue(by last trade): {values_by_last_traded_price[i]}")
                positions_sum += agent.position
                cash_sum += agent.cash
                values_by_last_trade_sum += market.last_traded_price * agent.position
            market.logger.info(f"Positions sum: {positions_sum}")
            market.logger.info(f"Cash sum: {cash_sum}")
            market.logger.info(f"Sum of values by last traded price: {values_by_last_trade_sum}")
            market.logger.info(f"Sum of values by fundamental: {sum(values_by_fundamental.values())}")
            market.logger.info(f"Midprices: {market.get_midprices()}")
            market.logger.info(f"Traded prices {market.traded_prices}")

            # valuations by agent:
            for agent_key, agent in market.agents.items():
                value_history = agent.position_value_history
                position_history = agent.position_history
                market.logger.info(f"\nAgent {str(agent_key)} value history\n: {value_history}")
                market.logger.info(f"\nAgent {str(agent_key)} position history\n: {position_history}")

                # plot it
                agent_file = f"{config.output_dir}/by_agents/agent_{str(agent_key)}_{str(agent)}.png"

                plot_agent_history(
                    position_history=position_history,
                    value_history=value_history,
                    output_file=agent_file,
                )

            # plot the security values history:
            traded_prices_float = {t: {v: float(price_item) for v, price_item in item.items()}
                                   for t, item in market.traded_prices.items()}
            df_candlestick = pd.DataFrame.from_dict(traded_prices_float,
                orient="index"
            )
            df_candlestick.index.name = "time"
            market.logger.info(df_candlestick.head())

            candlestick_filename = f"{config.output_dir}/candlestick_{str(market)}.png"
            plot_candlestick(df=df_candlestick, output_file=candlestick_filename, title=market.name)

            # plotting by type:
            plot_by_type(market.orders_by_agent_type, output_file=f"{config.output_dir}/orders_by_type_{str(market)}.png", title=f"Orders by type in {market.name}")
            plot_by_type(market.trades_by_agent_type,
                                output_file=f"{config.output_dir}/trades_by_type_{str(market)}.png", title=f"Trades by type in {market.name}")
            plot_by_type(market.trades_by_agent_type_ext,
                         output_file=f"{config.output_dir}/trades_by_type_ext_{str(market)}.png",
                         title=f"Trades by extended type in {market.name}", mode="extended")
            plot_bid_ask(market.bid_ask_history,
                         output_file=f"{config.output_dir}/bid_ask_history_{str(market)}.png",
                         title=f"Bid ask spread history {str(market)}")
            #calculate and plot realized volatility:
            window = 50
            volatility = market.calculate_realized_volatility(window=window)
            plot_realized_volatility(volatility=volatility,
                                     output_file=f"{config.output_dir}/realized_volatility_{str(market)}.png",
                                     title=f"Realized volatility {str(market)} with window {window}")


    def run(self) -> None:
        last_progress = -1

        for t in range(self.sim_time):
            self.logger.info(f"Step: {t}.", end='')
            self.step()
            progress = (step + 1) * 100 // total_steps

            if progress != last_progress:
                print(f"\rProgress: {progress:3d}%", end="", flush=True)
                last_progress = progress

        print()
        self.end_sim()

