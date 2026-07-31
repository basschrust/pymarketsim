import random
from typing import List
from loguru import logger
import pandas as pd

from marketsim.loggers import basic
from marketsim.market.price import Price
from marketsim.fourheap.constants import BUY, SELL
from marketsim.market.market import Market
from marketsim.fundamental.mean_reverting import GaussianMeanReverting
from marketsim.fundamental.lazy_mean_reverting import LazyGaussianMeanReverting
from marketsim.agent.zi_informed import ZIAgentInformed
from marketsim.agent.zi_not_informed import ZIAgentNotInformed
from marketsim.agent.market_maker_zoh import MMZOHAgent
from marketsim.agent.hbl_agent import HBLAgent
from marketsim.agent.agent import Agent
from marketsim.agent.market_maker import MMAgent
from marketsim.utils.id_generator import id_generator
from marketsim.plot.simple_plot import simple_plot
from marketsim.plot.candle import plot_candlestick
from marketsim.input import config


class Simulator:
    def __init__(self,
                 sim_time: int,
                 num_assets: int = 1,
                 lam: float = 0.1,
                 mean: float = 100.0,
                 r: float = .6,
                 shock_var=10,
                 #agent_groups: dict = {},
                 markets: dict = {},
                 q_max: int = 10,
                 pv_var: float = 5e6,
                 zi_shade: List = [Price(0.01), Price(0.02)], #AK [10, 30],
                 #num_mm_agents: int = 1,
                 #market_type:str = "discrete",  #discrete or continuous
                 ):
        print("Initializing simulation with following parameters...")

        self.num_assets = num_assets
        self.sim_time = sim_time
        self.lam = lam # lambda (activity factor)
        self.mean = mean
        self.r = r
        self.shock_var = shock_var # change propability of fundamental (market consensus) value

        self.current_time = 0
        self.markets = [] # each market serves single security

        self.agents = {} # but agents are now moved to markets

        for m_key, m_conf in markets.items():
            # TODO: take parameters from market conf
            fundamental = GaussianMeanReverting(mean=self.mean, final_time=self.sim_time, r=self.r,
                                                shock_var=self.shock_var)

            market = Market(fundamental=fundamental, time_steps=self.sim_time, market_type=m_conf["market_type"])

            self.markets.append(market)

            for group_name, agent_group in m_conf["agent_groups"].items():
                for i in range(agent_group["number"]):
                    # let's make it in case/ series of ifs to avoid security breach (if used the class name as code direcltly)
                    # ZI agents:
                    if agent_group["agent_class"] == "ZIAgentNotInformed":
                            agent = ZIAgentNotInformed(market=market, **agent_group["config"])
                            #self.add_agents([agent])
                            market.add_agents([agent])


                    # MMs:
                    if agent_group["agent_class"] == "MMZOHAgent":
                        agent = MMZOHAgent(market=market, **agent_group["config"])
                        # self.add_agents([agent])
                        market.add_agents([agent])

                    # HBL (Heuristic Belief)
                    if agent_group["agent_class"] == "HBLAgent":
                        agent = HBLAgent(market=market, **agent_group["config"])
                        # self.add_agents([agent])
                        market.add_agents([agent])

        return


    def add_agents(self, agents: list[Agent] | None) -> None:
        raise # moved to market
        for agent in agents:
            print(f"Adding agent {str(agent)}")
            self.agents[agent.get_id()] = agent

    def step(self) -> None:
        print(f'\nIt is time step {self.current_time}')
        for market in self.markets:
            cash_sum = 0
            for agent_id, agent in market.agents.items():
                cash_sum += agent.cash
            print(f"Asserting initial cash sum: {cash_sum}")
            assert cash_sum == 0
            for agent_id in market.agents:
                agent = market.agents[agent_id]
                if not agent.is_market_maker():
                    market.withdraw_all(agent_id) # AK: well, the market maker should not withdraw the orders
                                # so moving this to take_action?
                orders = agent.take_action(current_time=self.current_time) # but there should be different actions
                            # in different markets, solved: agents are defined inside a single market
                print(f'Agent {agent.agent_id} is entering the market {str(market)} and makes orders {orders}')
                market.add_orders(orders)
            print(f"Starting orders execution, matched queues should be empty here: {len(market.order_book.buy_matched.heap)}"
                  f" {len(market.order_book.sell_matched.heap)}")
            new_orders_matched = market.step(current_time=self.current_time)
            print(f"Starting to clear out orders.")

            for matched_order in new_orders_matched:
                print(f"Matched order {str(matched_order)}")
                market.record_trade(matched_order=matched_order)
            cash_sum = 0
            for agent_id, agent in market.agents.items():
                cash_sum += agent.cash
            print(f"Asserting cash sum: {cash_sum}")
            assert cash_sum == 0
            print(f'After clearing the market the last traded price is: {market.last_traded_price}')
            print(f'And the spread: {market.order_book.buy_unmatched.peek()} {market.order_book.sell_unmatched.peek()}')
            # update value of each agent in each market:
            for k, agent in market.agents.items():
                agent.record_valuation(current_time=self.current_time, price=market.last_traded_price)
        self.current_time += 1


    def end_sim(self) -> None:
        """ End the simulation and print summary """
        print(f"\n\nSimulation ended. time: {self.current_time}")
        for market in self.markets:
            print(f"Market {str(market)}:")
            fundamental_val = Price(market.get_final_fundamental())
            print(f"Final fundamental: {fundamental_val}")
            print(f"Orders matched: {len(market.matched_orders)}")
            print(f"Last traded price: {market.last_traded_price}")
            values_by_fundamental = {}
            values_by_last_traded_price = {}
            for agent_id in market.agents:
                agent = market.agents[agent_id]
                values_by_fundamental[agent_id] = Price(agent.get_pos_value()) + agent.position * fundamental_val + agent.cash
                values_by_last_traded_price[agent_id] = agent.position * market.last_traded_price + agent.cash
            print(f'At the end of the simulation we get valuations by fundamental: {values_by_fundamental}')
            positions_sum = 0
            cash_sum = 0
            values_by_last_trade_sum = 0
            for i, agent in market.agents.items():
                print(f"Agent {str(agent)}: \tposition: {agent.position}  \tcash: {agent.cash} "
                      f"\tvalue(by fund.): {values_by_fundamental[i]} \tvalue(by last trade): {values_by_last_traded_price[i]}")
                positions_sum += agent.position
                cash_sum += agent.cash
                values_by_last_trade_sum += market.last_traded_price * agent.position
            print(f"Positions sum: {positions_sum}")
            print(f"Cash sum: {cash_sum}")
            print(f"Sum of values by last traded price: {values_by_last_trade_sum}")
            print(f"Sum of values by fundamental: {sum(values_by_fundamental.values())}")
            print(f"Midprices: {market.get_midprices()}")
            print(f"Traded prices {market.traded_prices}")

            # valuations by agent:
            for agent_key, agent in market.agents.items():
                history = agent.position_value_history
                print(f"\nAgent {str(agent_key)} value history\n: {history}")

                # plot it
                agent_file = f"{config.output_dir}/agent_{str(agent_key)}_{str(agent)}.png"
                simple_plot(x=[i for i in history], y=[j for i, j in history.items()], output_file=agent_file)


            # plot the security values history:
            traded_prices_float = {t: {v: float(price_item) for v, price_item in item.items()}
                                   for t, item in market.traded_prices.items()}
            df_candlestick = pd.DataFrame.from_dict(traded_prices_float,
                orient="index"
            )
            df_candlestick.index.name = "time"
            print(df_candlestick.head())

            candlestick_filename = f"{config.output_dir}/candlestick_{str(market)}.png"
            plot_candlestick(df=df_candlestick, output_file=candlestick_filename)


    def run(self) -> None:
        for t in range(self.sim_time):
            print(f"Step: {t}.", end='')
            self.step()
        self.end_sim()
