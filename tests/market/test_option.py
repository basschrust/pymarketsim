import pytest

from marketsim.market import Security, Option
from marketsim.database.connectors.duckdb_storage import Repository

@pytest.fixture
def derivatives_config1(stock: Security):
    config1 = { "underlying": stock,
                "strike": 90,
                "expiration": 30,
                "option_side": "CALL",
                "option_type": "European",
                }
    return config1


################    test function         ###################

def test_create_option(stock: Security, repository: Repository, derivatives_config1: dict) -> None:
    option1 = Option(underlying=stock, repository=repository, derivatives_config=derivatives_config1)

    assert option1.underlying == stock
    assert option1 is not None

