import random
from typing import List

from fontTools.merge.util import current_time

from marketsim.fourheap.constants import BUY, SELL
from marketsim.market.market import Market
from marketsim.fundamental.mean_reverting import GaussianMeanReverting
from marketsim.fundamental.lazy_mean_reverting import LazyGaussianMeanReverting
from marketsim.agent.zi_informed import ZIAgentInformed
from marketsim.agent.zi_not_informed import ZIAgentNotInformed
from marketsim.agent.market_maker_zoh import MMZOHAgent
from marketsim.agent.agent import Agent
from marketsim.agent.market_maker import MMAgent
from marketsim.utils.id_generator import id_generator


class Simulator:
    def __init__(self,
                 num_background_zi_agents_informed: int,
                 num_background_zi_agents_not_informed: int,
                 sim_time: int,
                 num_assets: int = 1,
                 lam: float = 0.1,
                 mean: float = 100,
                 r: float = .6,
                 shock_var=10,
                 q_max: int = 10,
                 pv_var: float = 5e6,
                 zi_shade: List = [0.1,0.3], #AK [10, 30],
                 num_mm_agents: int = 1,
                 ):
        print("Initializing simulation with following parameters...")
        self.num_background_zi_agents_informed = num_background_zi_agents_informed
        self.num_background_zi_agents_not_informed = num_background_zi_agents_not_informed
        self.num_mm_agents = num_mm_agents
        self.num_assets = num_assets
        self.sim_time = sim_time
        self.lam = lam # activity factor
        self.current_time = 0

        self.markets = []
        for _ in range(num_assets):
            fundamental = GaussianMeanReverting(mean=mean, final_time=sim_time, r=r, shock_var=shock_var)
            # fundamental = LazyGaussianMeanReverting(mean=mean, final_time=sim_time, r=r, shock_var=shock_var)
            self.markets.append(Market(fundamental=fundamental, time_steps=sim_time))

        self.agents = {}
        for agent_id in range(num_background_zi_agents_informed):
            self.agents[agent_id] = (
                ZIAgentInformed(
                    market=self.markets[0],
                    q_max=q_max,
                    shade=zi_shade,
                    pv_var=pv_var
                ))

        for agent_id in range(num_background_zi_agents_informed, num_background_zi_agents_informed+num_background_zi_agents_not_informed):
            self.agents[agent_id] = (
                ZIAgentNotInformed(
                    market=self.markets[0],
                    q_max=q_max,
                    shade=zi_shade,
                    pv_var=pv_var
                ))

        for agent_id in range(num_background_zi_agents_not_informed + num_background_zi_agents_informed
                , num_background_zi_agents_informed + num_background_zi_agents_not_informed +num_mm_agents):
            self.agents[agent_id] = MMZOHAgent(agent_id=agent_id,
                                            market=self.markets[0],
                                            xi=0.04,
                                            K=3,
                                            omega=0.02,
                                            )

    def add_agents(self, agents: list[Agent] | None) -> None:
        for agent in agents:
            print(f"Adding agent {str(agent)}")
            self.agents[agent.get_id()] = agent

    def step(self) -> None:
        print(f'It is time step {self.current_time}')
        for market in self.markets:
            for agent_id in self.agents:
                #if random.random() <= self.lam:
                agent = self.agents[agent_id]
                if not agent.is_market_maker():
                    market.withdraw_all(agent_id) # AK: well, the market maker should not withdraw the orders
                                # so moving this to take_action?
                orders = agent.take_action(current_time=self.current_time)
                print(f'Agent {agent.agent_id} is entering the market and makes orders {orders}')
                market.add_orders(orders)
            new_orders = market.step(current_time=self.current_time)
            for matched_order in new_orders:
                print(f"Matching order {str(matched_order)}")
                agent_id = matched_order.order.agent_id
                quantity = matched_order.order.order_type * matched_order.order.quantity
                cash = -matched_order.price * matched_order.order.quantity * matched_order.order.order_type
                market.last_traded_price = matched_order.price
                self.agents[agent_id].update_position(quantity=quantity, cash=cash)
        self.current_time += 1


    def end_sim(self) -> None:
        print(f"\n\nSimulation ended. time: {self.current_time}")
        fundamental_val = self.markets[0].get_final_fundamental()
        print(f"Final fundamental: {fundamental_val}")
        print(f"Orders matched: {len(self.markets[0].matched_orders)}")
        print(f"Last traded price: {self.markets[0].last_traded_price}")
        values_by_fundamental = {}
        values_by_last_traded_price = {}
        for agent_id in self.agents:
            agent = self.agents[agent_id]
            values_by_fundamental[agent_id] = agent.get_pos_value() + agent.position * fundamental_val + agent.cash
            values_by_last_traded_price[agent_id] = agent.position * self.markets[0].last_traded_price + agent.cash
        print(f'At the end of the simulation we get valuations by fundamental: {values_by_fundamental}')
        positions_sum = 0
        cash_sum = 0
        values_by_last_trade_sum = 0
        for i, agent in self.agents.items():
            print(f"Agent {str(agent)}: \tposition: {agent.position}  \tcash: {agent.cash} "
                  f"\tvalue(by fund.): {values_by_fundamental[i]} \tvalue(by last trade): {values_by_last_traded_price[i]}")
            positions_sum += agent.position
            cash_sum += agent.cash
            values_by_last_trade_sum += self.markets[0].last_traded_price * agent.position
        print(f"Positions sum: {positions_sum}")
        print(f"Cash sum: {cash_sum}")
        print(f"Sum of values by last traded price: {values_by_last_trade_sum}")
        print(f"Sum of values by fundamental: {sum(values_by_fundamental.values())}")
        print(f"Midprices: {self.markets[0].get_midprices()}")

    def run(self) -> None:
        print(f"Agents ({len(self.agents)}):")
        for agent_id in range(len(self.agents)):
            print(f"{agent_id}: {str(self.agents[agent_id])}")
        # the core - running simulation steps:
        for t in range(self.sim_time):
            print(f"Step: {t}.", end='')
            self.step()
        self.end_sim()
