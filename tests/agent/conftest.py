import pytest

from marketsim.database.connectors.duckdb_storage import Repository
from marketsim.market import Security, Option
from marketsim.agent import (Agent, NoiseAgent, HBLAgent, MMZOHAgent, MomentumAgent, OptionMMZOHAgent, SpoofingAgent,
        WashTradingAgent, ZIAgentNotInformed)


@pytest.fixture
def agent_noise(security: Security, repository: Repository):
    return NoiseAgent(markets=[security], repository=repository)

@pytest.fixture
def agent_hbl(security: Security, repository: Repository):
    return HBLAgent(markets=[security], repository=repository)

@pytest.fixture
def agent_mm(security: Security, repository: Repository):
    return MMZOHAgent(markets=[security], repository=repository)

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

