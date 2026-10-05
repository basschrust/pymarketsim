import pytest

from marketsim.fourheap.order import Order
from marketsim.market import Price


BUY = 1
SELL = -1


def make_order(
    price=100,
    order_type=BUY,
    quantity=10,
    agent_id=1,
    time=1,
    asset_id=1,
):
    return Order(
        price=Price(price),
        order_type=order_type,
        quantity=quantity,
        agent_id=agent_id,
        time=time,
        asset_id=asset_id,
    )


def test_order_creation():
    order = make_order()

    assert order.price == Price(100)
    assert order.order_type == BUY
    assert order.quantity == 10
    assert order.agent_id == 1
    assert order.time == 1
    assert order.asset_id == 1

    assert order.order_id is not None
    assert order.parent_id is None
    assert order.matched_with is None
    assert order.valid_until is None
    assert order.executed_price is None
    assert order.executed_mode is None


def test_order_ids_are_unique():
    order1 = make_order()
    order2 = make_order()

    assert order1.order_id != order2.order_id


def test_price_must_be_positive():
    with pytest.raises(ValueError, match="Price must be greater than 0"):
        make_order(price=0)

    with pytest.raises(ValueError, match="Price must be greater than 0"):
        make_order(price=-10)


def test_update_quantity_filled():
    order = make_order(quantity=10)

    order.update_quantity_filled(3)

    assert order.quantity == 7


def test_merge_order():
    order = make_order(quantity=10)

    order.merge_order(5)

    assert order.quantity == 15


def test_copy_and_decrease():
    order = make_order(quantity=10)

    remaining_order = order.copy_and_decrease(3)

    # Original order represents the executed part
    assert order.quantity == 3

    # New order represents the remaining part
    assert remaining_order.quantity == 7


def test_copy_and_decrease_preserves_order_properties():
    order = Order(
        price=Price(123.45),
        order_type=SELL,
        quantity=10,
        agent_id=42,
        time=17,
        asset_id=5,
        valid_until=100,
    )

    remaining_order = order.copy_and_decrease(3)

    assert remaining_order.price == Price(123.45)
    assert remaining_order.order_type == SELL
    assert remaining_order.quantity == 7
    assert remaining_order.agent_id == 42
    assert remaining_order.time == 17
    assert remaining_order.asset_id == 5
    assert remaining_order.valid_until == 100

    # It must be a new order
    assert remaining_order.order_id != order.order_id

    # And it must remember its parent
    assert remaining_order.parent_id == order.order_id


def test_order_equality_is_based_on_order_id():
    order1 = make_order()
    order2 = make_order()

    assert order1 != order2
    assert order1 == order1
    assert order1 != None


def test_sell_order_priority():
    cheaper = make_order(price=99, order_type=SELL, time=1)
    more_expensive = make_order(price=101, order_type=SELL, time=2)

    assert cheaper > more_expensive


def test_buy_order_priority():
    more_expensive = make_order(price=101, order_type=BUY, time=1)
    cheaper = make_order(price=99, order_type=BUY, time=2)

    assert more_expensive > cheaper
    