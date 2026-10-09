import pytest

from marketsim.database.connectors.duckdb_storage import Repository
from marketsim.market import Security, Option, Price
from tests.conftest import repository, option_tnt_call
from marketsim.agent import Agent, NoiseAgent


@pytest.fixture
def derivatives_config1(stock: Security):
    config1 = { "underlying": stock,
                "strike": Price(90),
                "expiration": 30,
                "option_side": "CALL",
                "option_type": "European",
                }
    return config1


