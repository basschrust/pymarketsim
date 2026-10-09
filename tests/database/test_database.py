import pytest

import pandas as pd

from marketsim.database.connectors.duckdb_storage import Repository
from marketsim.market import Security, Price, Option
from marketsim.agent import Agent


EXPECTED_TABLES = {"securities",
                   "options",
                   "agents",
                    "position_history",
                    "eod_positions",
                    "portfolio_value_history",
                    "eod_portfolio_value",
                    "cash_history",
                    "eod_cash",
                    "traded_prices",
                    "eod_prices",
                    "orders",
                    "trades",
                    "option_expiration"}


###### test functions  #####


def test_database_creation(repository: Repository):
    assert repository is not None
    assert repository.localdb.name == "daedalus.duckdb"


def test_expected_tables_exist(repository):
    rows = repository.connection.execute("SHOW TABLES").fetchall()
    actual_tables = {row[0] for row in rows}

    assert EXPECTED_TABLES <= actual_tables


def test_tables_are_empty_at_initialization(repository):
    for table in EXPECTED_TABLES:
        count = repository.connection.execute(
            f'SELECT COUNT(*) FROM "{table}"'
        ).fetchone()[0]

        assert count == 0, f"Table {table!r} should be empty, got {count} rows"



####  getting data

@pytest.mark.usefixtures("position_history_1")
def test_get_eod_positions_filters_by_agent(repository: Repository):
    actual = repository.get_eod_positions(agent_id=1)

    expected = pd.DataFrame({
        "day": [0, 0],
        "asset_id": [0, 1],
        "position": [100, 50],
    })

    actual = actual.sort_values("asset_id").reset_index(drop=True)

    pd.testing.assert_frame_equal(actual, expected)


def test_get_eod_prices(repository: Repository):
    actual = repository.get_eod_prices(asset_id=1)

    # actual = actual.sort_values("asset_id").reset_index(drop=True)

    expected = pd.DataFrame({
        "day": [0, 0],
        "asset_id": [0, 1],
        "position": [100, 50],
    })

    pd.testing.assert_frame_equal(actual, expected)

def test_get_eod_cash(repository: Repository):
    actual = repository.get_eod_cash(agent_id=1)

    # actual = actual.sort_values("asset_id").reset_index(drop=True)

    expected = pd.DataFrame({
        "day": [0, 0],
        "asset_id": [0, 1],
        "position": [100, 50],
    })

    pd.testing.assert_frame_equal(actual, expected)

def test_get_eod_portfolio_values(repository: Repository):
    actual = repository.get_eod_portfolio_values(agent_id=1)

    # actual = actual.sort_values("asset_id").reset_index(drop=True)

    expected = pd.DataFrame({
        "day": [0, 0],
        "asset_id": [0, 1],
        "position": [100, 50],
    })

    pd.testing.assert_frame_equal(actual, expected)



## saving data:

def test_save_security(repository: Repository,
                       stock_tnt: Security):
    #repository.save_security(stock_tnt)

    ret = repository.connection.execute("""SELECT s.asset_id,
                                                  s.instrument_class,
                                                  s.market_type,
                                                  s.name,
                                                  s.eod_status,
                                                  s.reference_price
                                          FROM securities s""").fetchdf()

    # TODO: duplicates?  there are currently 2 rows as Security.__init__  already saves the security
    assert ret is not None
    assert ret.shape == (1, 6)
    assert ret[0].asset_id == stock_tnt.asset_id


def test_save_agent(repository: Repository,
                    agent_long_put_option_expiration_day: Agent):

    agent = agent_long_put_option_expiration_day

    repository.save_agent(agent=agent)

    ret = repository.connection.execute("""SELECT
                                                agent_id,
                                                name,
                                                group_name,
                                                configuration
                                            FROM agents""").fetchdf()

    assert ret is not None
    assert ret.shape == (1, 4)


def test_save_position_history(repository: Repository,
                               agent_3k_mit_2k_tnt: Agent):
    agent = agent_3k_mit_2k_tnt

    repository.save_position_history()

    ret = repository.connection.execute("""SELECT *
                        FROM position_history """).fetchall()

    assert ret is not None
    assert ret.shape == (1, 5)


def test_save_eod_position(repository: Repository,
                           agent_sophisticated_1: Agent):
    agent = agent_sophisticated_1
    agent.eod()

    ret = repository.connection.execute("""SELECT *
                FROM eod_positions """).fetchall()

    assert ret.shape == (2, 6)


def test_save_portfolio_value_history(repository: Repository,
                                      agent_sophisticated_1: Agent):
    agent = agent_sophisticated_1
    agent.eod()

    ret = repository.connection.execute("""SELECT *
                FROM portfolio_value_history""").fetchdf()

    assert ret.shape == (1,4)


def test_save_eod_portfolio_value(repository: Repository,
                                  agent_sophisticated_1: Agent):
    agent = agent_sophisticated_1
    agent.eod()

    ret = repository.connection.execute("""SELECT *
                FROM eod_portfolio_value  """).fetchdf()

    assert ret.shape == (2, 6)


def test_save_cash_history(repository: Repository,
                           agent_sophisticated_1: Agent):
    agent = agent_sophisticated_1
    agent.eod()
    ret = repository.connection.execute("""SELECT *
            FROM cash_history""").fetch_df()


    assert ret.shape == (1, 6)


def test_save_eod_cash(repository: Repository,
                       agent_sophisticated_1: Agent):
    agent = agent_sophisticated_1
    agent.eod()

    ret = repository.connection.execute("""SELECT *
            FROM eod_cash""").fetch_df()

    assert ret.shape == (1, 3)

def test_save_eod_cash_2(repository: Repository,
                       agent_sophisticated_1: Agent):
    agent = agent_sophisticated_1
    agent.eod()
    # two days so two records are saved
    agent.sod()
    agent.eod()

    ret = repository.connection.execute("""SELECT *
            FROM eod_cash""").fetch_df()

    assert ret.shape == (2, 3)


def test_save_traded_prices(repository: Repository):
    assert 1 == 1

def test_save_eod_prices(repository: Repository):
    assert 1 == 1

def test_save_orders(repository: Repository):
    assert 1 == 1

def test_save_trades(repository: Repository):
    assert 1 == 1

def test_save_option_expiration(repository: Repository,
                                option_call_before_expiration_itm):
    assert 1 == 1

