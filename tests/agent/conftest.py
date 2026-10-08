import pytest

from marketsim.database.connectors.duckdb_storage import Repository
from marketsim.market import Security, Option
from marketsim.agent import (Agent, NoiseAgent, HBLAgent, MMZOHAgent, MomentumAgent, OptionMMZOHAgent, SpoofingAgent,
        WashTradingAgent, ZIAgentNotInformed)

BUY = 1
SELL = -1

@pytest.fixture
def agent_noise(stock_tnt: Security, stock_mit: Security, repository: Repository):
    return NoiseAgent(markets=[stock_tnt, stock_mit], repository=repository)

@pytest.fixture
def agent_hbl(security: Security, repository: Repository):
    return HBLAgent(markets=[security], repository=repository)

@pytest.fixture
def agent_mm(stock_tnt: Security, stock_mit:Security, repository: Repository):
    return MMZOHAgent(markets=[stock_tnt, stock_mit], repository=repository)

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
