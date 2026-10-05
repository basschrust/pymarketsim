import pytest

from marketsim.fourheap.order import Order
from marketsim.market import Price
from marketsim.fourheap import FourHeap


BUY = 1
SELL = -1




#############   test functions  #############################33

def test_order_creation(buy_order):
    assert buy_order.price == Price(100)
    assert buy_order.order_type == BUY
    assert buy_order.quantity == 10
    assert buy_order.agent_id == 1
    assert buy_order.time == 1
    assert buy_order.asset_id == 1

    assert buy_order.order_id is not None
    assert buy_order.parent_id is None
    assert buy_order.matched_with is None
    assert buy_order.valid_until is None
    assert buy_order.executed_price is None
    assert buy_order.executed_mode is None


def test_order_ids_are_unique(order_factory):
    order1 = order_factory()
    order2 = order_factory()

    assert order1.order_id != order2.order_id


def test_price_must_be_positive(order_factory):
    with pytest.raises(ValueError, match="Price must be greater than 0"):
        order_factory(price=0)

    with pytest.raises(ValueError, match="Price must be greater than 0"):
        order_factory(price=-10)


def test_copy_and_decrease(order_factory):
    order = order_factory(quantity=10)

    remaining_order = order.copy_and_decrease(3)

    assert order.quantity == 3
    assert remaining_order.quantity == 7
    assert remaining_order.order_id != order.order_id
    assert remaining_order.parent_id == order.order_id


# old tests before fixtures were set:


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

    assert order.price == Price(123.45)
    assert order.order_type == SELL
    assert order.quantity == 3
    assert order.agent_id == 42
    assert order.time == 17
    assert order.asset_id == 5
    assert order.valid_until == 100

    # It must be a new order
    assert remaining_order.order_id != order.order_id

    # And it must remember its parent
    assert remaining_order.parent_id == order.order_id


def test_large_sell_order_against_many_small_buy_orders(stock):
    fourheap = FourHeap(market=stock)

    number_of_orders = 2493

    # Rest 2493 BUY orders, each for one share.
    for i in range(number_of_orders):
        order = Order(
            price=Price(100.1),
            order_type=BUY,
            quantity=1,
            agent_id=i,
            time=i,
            asset_id=1,
        )
        fourheap.insert(order)

    assert fourheap.buy_unmatched.size == number_of_orders
    assert fourheap.sell_unmatched.size == 0

    # One large SELL order.
    sell_order = Order(
        price=Price(100),
        order_type=SELL,
        quantity=number_of_orders,
        agent_id=9999,
        time=number_of_orders + 1,
        asset_id=1,
    )

    fourheap.insert(sell_order)

    # The whole incoming order was executed.
    # AK - well, the sell should be split to 2493 orders here?
    # assert sell_order.quantity == number_of_orders

    # All resting BUY liquidity was consumed.
    assert fourheap.buy_unmatched.size == 0

    # Nothing remains on the SELL side.
    assert fourheap.sell_unmatched.size == 0

    # Every one-share BUY order became a matched order.
    assert fourheap.buy_matched.size == number_of_orders


def test_large_sell_order_leaves_remaining_quantity(stock):
    fourheap = FourHeap(market=stock)

    resting_quantity = 2000
    incoming_quantity = 2493

    for i in range(resting_quantity):
        order = Order(
            price=Price(100),
            order_type=BUY,
            quantity=1,
            agent_id=i,
            time=i,
            asset_id=1,
        )
        fourheap.insert(order)

    sell_order = Order(
        price=Price(99.8),
        order_type=SELL,
        quantity=incoming_quantity,
        agent_id=9999,
        time=resting_quantity + 1,
        asset_id=1,
    )

    fourheap.insert(sell_order)

    # The incoming Order object represents the executed portion.
    # AK - no, it is split to unit orders?
    # assert sell_order.quantity == resting_quantity

    # All resting BUY orders were consumed.
    assert fourheap.buy_unmatched.size == 0

    # 493 shares remain as a new SELL order.
    assert fourheap.sell_unmatched.size == (
        incoming_quantity - resting_quantity
    )
