import pytest

from marketsim.database.connectors.duckdb_storage import Repository
from marketsim.market import Security
from marketsim.agent import (Agent, NoiseAgent, HBLAgent, MMZOHAgent, MomentumAgent, OptionMMZOHAgent, SpoofingAgent,
        WashTradingAgent, ZIAgentNotInformed)


@pytest.fixture
def noise_agent(security: Security, repository: Repository):
    return NoiseAgent(markets=[security], repository=repository)





