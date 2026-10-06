import pytest

from marketsim.database.connectors.duckdb_storage import Repository
from marketsim.fourheap.order import Order
from marketsim.market import Price, Security, Option


BUY = 1
SELL = -1


@pytest.fixture
def order_factory():
    def _create_order(
        price=100,
        order_type=BUY,
        quantity=10,
        agent_id=1,
        time=1,
        asset_id=1,
        valid_until=None,
    ):
        return Order(
            price=Price(price),
            order_type=order_type,
            quantity=quantity,
            agent_id=agent_id,
            time=time,
            asset_id=asset_id,
            valid_until=valid_until,
        )

    return _create_order


@pytest.fixture
def buy_order(order_factory):
    return order_factory()


@pytest.fixture
def sell_order(order_factory):
    return order_factory(order_type=SELL)

@pytest.fixture
def repository():
    return Repository()

@pytest.fixture
def stock(repository: Repository):
    return Security(reference_price=Price(95.00), name="stock1", repository=repository,
                    market_type="continuous", instrument_class="stock")

@pytest.fixture
def stock_tnt(repository: Repository):
    return Security(reference_price=Price(167.00), name="stock TNT", repository=repository,
                    market_type="continuous", instrument_class="stock")


@pytest.fixture
def security(repository: Repository):
    return Security(reference_price=Price(101.00), name="stock1", repository=repository,
                    market_type="continuous", instrument_class="stock")

@pytest.fixture
def security_with_trades(repository: Repository):
    sec = Security(reference_price=Price(101.00), name="stock1", repository=repository,
                    market_type="continuous", instrument_class="stock")
    # TODO: add trade
    return sec

@pytest.fixture
def security_after_sod(repository: Repository):
    sec = Security(reference_price=Price(101.00), name="stock1", repository=repository,
                    market_type="continuous", instrument_class="stock")
    sec.sod()
    return sec

@pytest.fixture
def security_abandoned(repository: Repository, security: Security):
    # an expired option or other security that trading is not allowed any more
    security.status = "abandoned"
    return security

### derivatives:

@pytest.fixture
def option_config_call() -> dict:
    conf = {
        "strike": Price(90.00),
        "option_side": "CALL",
        "option_type": "European",
        "expiration": 10,
            }
    return conf

@pytest.fixture
def option_config_put() -> dict:
    conf = {
        "strike": Price(90.00),
        "option_side": "PUT",
        "option_type": "European",
        "expiration": 10,
            }
    return conf


@pytest.fixture
def option_tnt_call(repository: Repository, stock_tnt: Security, option_config_call: dict):
    option = Option(repository=repository, underlying=stock_tnt, derivatives_config=option_config_call)
    return option

@pytest.fixture
def option_tnt_put(repository: Repository, stock_tnt: Security, option_config_put: dict):
    option = Option(repository=repository, underlying=stock_tnt, derivatives_config=option_config_put)
    return option
