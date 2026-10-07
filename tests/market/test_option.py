import pytest

from marketsim.market import Security, Option, Price
from marketsim.database.connectors.duckdb_storage import Repository




################    test functions         ###################

def test_create_option(stock: Security, repository: Repository, derivatives_config1: dict) -> None:
    option1 = Option(underlying=stock, repository=repository, derivatives_config=derivatives_config1)

    assert option1.underlying == stock
    assert option1 is not None

def test_option_call_itm(stock_tnt: Security,
                                  repository: Repository,
                                  option_call_before_expiration_itm: Option) -> None:
    option = option_call_before_expiration_itm

    assert option is not None
    # TODO: check BS price?
    assert option.get_theoretical_price() > 0, "CALL ITM has positive price"

###  trading



#### expiration / exercise ###

def test_exercise_option_call_itm_before(stock_tnt: Security,
                                  repository: Repository,
                                  option_call_before_expiration_itm: Option) -> None:
    option = option_call_before_expiration_itm
    premium = option.exercise()

    assert option is not None
    assert option.get_theoretical_price() > 0, "CALL ITM has positive price"
    assert premium == 0, "Premium before expiration should be 0"
    # TODO: agents cashflows check? - another test


def test_exercise_option_call_itm_exp_day(stock_tnt: Security,
                                  repository: Repository,
                                  option_call_at_expiration_itm: Option) -> None:
    option = option_call_at_expiration_itm
    premium = option.exercise()

    assert option is not None
    assert option.get_theoretical_price() > 0, "CALL ITM has positive price"
    assert premium == stock_tnt.last_traded_price - option.strike, "Premium at expiration should S-K"


def test_exercise_option_put_itm_before(stock_tnt: Security,
                                  repository: Repository,
                                  option_put_before_expiration_itm: Option) -> None:
    option = option_put_before_expiration_itm
    premium = option.exercise()

    assert option is not None
    assert option.get_theoretical_price() > 0, "CALL ITM has positive price"
    assert premium == 0, "Premium before expiration should be 0"
    # TODO: agents cashflows check? - another test


def test_exercise_option_put_itm_exp_day(stock_tnt: Security,
                                  repository: Repository,
                                  option_put_at_expiration_itm: Option) -> None:
    option = option_put_at_expiration_itm
    stock_tnt.last_traded_price = Price(67)
    premium = option.exercise()

    assert option is not None
    assert premium == - stock_tnt.last_traded_price + option.strike, "Premium at expiration is K-S"


@pytest.mark.xfail(reason="Take option on exercise day!")
def test_exercise_option_call_otm(stock_tnt: Security,
                                  repository: Repository,
                                  option_tnt_call: Option) -> None:
    stock_tnt.last_traded_price = Price(86.00) # to be under strike which is 90
    option_tnt_call.eod()

    assert option_tnt_call.get_theoretical_price() == 4.0, "Premium should be 0"


def test_exercise_option_put_itm(stock_tnt: Security, repository: Repository, option_tnt_call: Option) -> None:
    assert 1 == 1


def test_exercise_option_put_otm(stock_tnt: Security, repository: Repository, option_tnt_call: Option) -> None:
    assert 1 == 1


### reporting


