import pytest
from pathlib import Path

from marketsim.database.connectors.duckdb_storage import Repository
from marketsim.fourheap.order import Order
from marketsim.market import Price, Security, Option
from marketsim.agent import Agent, MMZOHAgent, NoiseAgent, HBLAgent


BUY = 1
SELL = -1

tmp_path = Path("tmp")

@pytest.fixture
def repository(tmp_path: Path):
    repo = Repository(output_dir=tmp_path)
    yield repo
    repo.connection.close()



@pytest.fixture
def order_factory():
    def _create_order(
        price:int=100,
        order_type:int=BUY,
        quantity:int=10,
        agent_id:int=1,
        time:int=1,
        asset_id:int=1,
        valid_until:int|None=None,
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
def buy_order_99(order_factory):
    return order_factory(price=99, order_type=BUY)

@pytest.fixture
def buy_order_101(order_factory):
    return order_factory(price=101, order_type=BUY)

@pytest.fixture
def sell_order(order_factory):
    return order_factory(order_type=SELL)

@pytest.fixture
def sell_order_99(order_factory):
    return order_factory(price=99, order_type=SELL)

@pytest.fixture
def sell_order_101(order_factory):
    return order_factory(price=101, order_type=SELL)


@pytest.fixture
def stock(repository: Repository):
    return Security(reference_price=Price(95.00), name="stock1", repository=repository,
                    market_type="continuous", instrument_class="stock")

@pytest.fixture
def stock_tnt(repository: Repository):
    return Security(reference_price=Price(167.00), name="stock TNT", repository=repository,
                    market_type="continuous", instrument_class="stock", short_name="TNT")

@pytest.fixture
def stock_mit(repository: Repository):
    return Security(reference_price=Price(18.61), name="stock MIT", repository=repository,
                    market_type="continuous", instrument_class="stock", short_name="MIT")


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

### agents:

@pytest.fixture
def agent_noise(stock_tnt: Security, stock_mit: Security, repository: Repository):
    return NoiseAgent(markets=[stock_tnt, stock_mit], repository=repository)

@pytest.fixture
def agent_hbl(security: Security, repository: Repository):
    return HBLAgent(markets=[security], repository=repository)

@pytest.fixture
def agent_mm(stock_tnt: Security, stock_mit:Security, repository: Repository):
    return MMZOHAgent(markets=[stock_tnt, stock_mit], repository=repository)



