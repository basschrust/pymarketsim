import pytest

from marketsim.database.connectors.duckdb_storage import Repository
from marketsim.fourheap.order import Order
from marketsim.market import Price, Security


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
    return Security(reference_price=Price(100.00), name="stock1", repository=repository,
                    market_type="continuous", instrument_class="stock")

