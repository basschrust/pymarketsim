import pytest

from marketsim.database.connectors.duckdb_storage import Repository


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
