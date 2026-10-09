import pytest

from marketsim.database.connectors.duckdb_storage import Repository
from marketsim.market import Security, Option
from marketsim.agent import (Agent, NoiseAgent, HBLAgent, MMZOHAgent, MomentumAgent, OptionMMZOHAgent, SpoofingAgent,
        WashTradingAgent, ZIAgentNotInformed)

BUY = 1
SELL = -1


@pytest.fixture
def agent_momentum(security: Security, repository: Repository):
    return MomentumAgent(markets=[security], repository=repository)

@pytest.fixture
def agent_spoof(security: Security, repository: Repository):
    return SpoofingAgent(markets=[security], repository=repository)

@pytest.fixture
def agent_washtrader(security: Security, repository: Repository):
    return WashTradingAgent(markets=[security], repository=repository)

@pytest.fixture
def agent_zi(security: Security, repository: Repository):
    return ZIAgentNotInformed(markets=[security], repository=repository)

@pytest.fixture
def agent_option_mm(security: Security, option: Option, repository: Repository):
    return OptionMMZOHAgent(markets=[security], repository=repository)

######### for cash flow check between agents:

@pytest.fixture
def buy_order_tnt(order_factory,
                     stock_tnt: Security,
                     agent_noise: Agent):
    return order_factory(agent_id=agent_noise.agent_id, asset_id=stock_tnt.asset_id)

@pytest.fixture
def buy_order_99_tnt(order_factory,
                     stock_tnt: Security,
                     agent_noise: Agent):
    return order_factory(price=99, order_type=BUY, agent_id=agent_noise.agent_id, asset_id=stock_tnt.asset_id)

@pytest.fixture
def buy_order_101_tnt(order_factory,
                     stock_tnt: Security,
                     agent_noise: Agent):
    return order_factory(price=101, order_type=BUY, agent_id=agent_noise.agent_id, asset_id=stock_tnt.asset_id)

@pytest.fixture
def sell_order_tnt(order_factory,
                     stock_tnt: Security,
                     agent_mm: Agent):
    return order_factory(order_type=SELL, agent_id=agent_mm.agent_id, asset_id=stock_tnt.asset_id)

@pytest.fixture
def sell_order_99_tnt(order_factory,
                     stock_tnt: Security,
                     agent_mm: Agent):
    return order_factory(price=99, order_type=SELL, agent_id=agent_mm.agent_id, asset_id=stock_tnt.asset_id)

@pytest.fixture
def sell_order_101_tnt(order_factory,
                     stock_tnt: Security,
                     agent_mm: Agent):
    return order_factory(price=101, order_type=SELL, agent_id=agent_mm.agent_id, asset_id=stock_tnt.asset_id)

# MIT orders

@pytest.fixture
def sell_order_101_mit(order_factory,
                     stock_mit: Security,
                     agent_mm: Agent):
    return order_factory(price=101, order_type=SELL, agent_id=agent_mm.agent_id, asset_id=stock_mit.asset_id)

@pytest.fixture
def buy_order_102_mit_5(order_factory,
                     stock_mit: Security,
                     agent_noise: Agent):
    return order_factory(price=102,
                         order_type=BUY,
                         agent_id=agent_noise.agent_id,
                         asset_id=stock_mit.asset_id,
                         quantity=5)

@pytest.fixture
def buy_order_101_mit(order_factory,
                     stock_mit: Security,
                     agent_noise: Agent):
    return order_factory(price=101, order_type=BUY, agent_id=agent_noise.agent_id, asset_id=stock_mit.asset_id)


##### agents with open positions

@pytest.fixture
def agent_3k_mit_2k_tnt(agent_noise: Agent,
                        stock_mit: Security,
                        stock_tnt: Security):
    stock_tnt.add_agents([agent_noise])
    stock_mit.add_agents([agent_noise])
    agent_noise.position[stock_tnt.asset_id] = 2000
    agent_noise.position[stock_mit.asset_id] = 3000

    agent_noise.record_valuation(current_time=0)

    return agent_noise

