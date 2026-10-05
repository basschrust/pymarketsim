import pytest
from decimal import Decimal

from marketsim.market import Price

############    test functions  ###############


def test_price_create():
    price = Price(98.00)

    assert price == Decimal("98.00")

def test_price_update():
    price = Price(98.00)

    price += Price(3.00)

    assert price == Price(101.00)


def test_price_multiplication():
    price = Price(98.00)
    price2 = 2 * price

    assert price2 == Price(196.00)
