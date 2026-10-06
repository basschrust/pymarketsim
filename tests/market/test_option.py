import pytest

from marketsim.market import Security, Option
from marketsim.database.connectors.duckdb_storage import Repository




################    test functions         ###################

def test_create_option(stock: Security, repository: Repository, derivatives_config1: dict) -> None:
    option1 = Option(underlying=stock, repository=repository, derivatives_config=derivatives_config1)

    assert option1.underlying == stock
    assert option1 is not None


###  trading



#### expiration / exercise ###

def test_exercise_option_call_itm(stock_tnt: Security, repository: Repository, option_tnt_call: Option) -> None:
    assert 1 == 1


def test_exercise_option_call_otm(stock_tnt: Security, repository: Repository, option_tnt_call: Option) -> None:
    assert 1 == 1


def test_exercise_option_put_itm(stock_tnt: Security, repository: Repository, option_tnt_call: Option) -> None:
    assert 1 == 1


def test_exercise_option_put_otm(stock_tnt: Security, repository: Repository, option_tnt_call: Option) -> None:
    assert 1 == 1


### reporting


