import random
from typing import List

from marketsim.fourheap.constants import BUY, SELL
from marketsim.market.market import Market
from marketsim.fundamental.mean_reverting import GaussianMeanReverting
from marketsim.fundamental.lazy_mean_reverting import LazyGaussianMeanReverting
from marketsim.agent.zero_intelligence_agent import ZIAgent
from marketsim.agent.market_maker import MMAgent
from marketsim.utils.id_generator import id_generator



class Simulator:
    def __init__(self,
                 num_background_zi_agents: int,
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
        print("Initializing simulation...")
        self.num_zi_agents = num_background_zi_agents
        self.num_mm_agents = num_mm_agents
        self.num_assets = num_assets
        self.sim_time = sim_time
        self.lam = lam
        self.time = 0

        self.markets = []
        for _ in range(num_assets):
            fundamental = GaussianMeanReverting(mean=mean, final_time=sim_time, r=r, shock_var=shock_var)
            # fundamental = LazyGaussianMeanReverting(mean=mean, final_time=sim_time, r=r, shock_var=shock_var)
            self.markets.append(Market(fundamental=fundamental, time_steps=sim_time))

        self.agents = {}
        for agent_id in range(num_background_zi_agents):
            self.agents[agent_id] = (
                ZIAgent(
                    agent_id=agent_id,
                    market=self.markets[0],
                    q_max=q_max,
                    shade=zi_shade,
                    pv_var=pv_var
                ))

        for agent_id in range(num_background_zi_agents, num_background_zi_agents+num_mm_agents):
            self.agents[agent_id] = MMAgent(agent_id=agent_id,
                                            market=self.markets[0],
                                            xi=0.1,
                                            K=3,
                                            omega=0.01,
                                            )

    def step(self):
        # print(f'It is time step {self.time}')
        for market in self.markets:
            for agent_id in self.agents:
                if random.random() <= self.lam:
                    agent = self.agents[agent_id]
                    market.withdraw_all(agent_id)
                    orders = agent.take_action()
                    # print(f'Agent {agent.agent_id} is entering the market and makes order {order}')
                    market.add_orders(orders)
            new_orders = market.step()
            for matched_order in new_orders:
                agent_id = matched_order.order.agent_id
                quantity = matched_order.order.order_type * matched_order.order.quantity
                cash = -matched_order.price * matched_order.order.quantity * matched_order.order.order_type
                self.agents[agent_id].update_position(quantity, cash)
        self.time += 1


    def end_sim(self):
        fundamental_val = self.markets[0].get_final_fundamental()
        print(f"Final fundamental: {fundamental_val}")
        print(f"Orders matched: {len(self.markets[0].matched_orders)}")
        values = {}
        for agent_id in self.agents:
            agent = self.agents[agent_id]
            values[agent_id] = agent.get_pos_value() + agent.position * fundamental_val + agent.cash
        print(f'At the end of the simulation we get {values}')

    def run(self):
        print("go!")
        for t in range(self.sim_time):
            self.step()
        self.end_sim()
