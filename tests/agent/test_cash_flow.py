import pytest

from marketsim.market import Security, Price
from marketsim.fourheap import Order
from marketsim.agent import MMZOHAgent
from marketsim.market import Security
from marketsim.agent import NoiseAgent, Agent
from tests.conftest import stock_tnt





#####   test  functions ##########

def test_cf_1(stock_tnt: Security,
              agent_noise: NoiseAgent,
              buy_order_101_tnt: Order,
              agent_mm: MMZOHAgent,
              sell_order_99_tnt: Order):

    stock_tnt.add_agents([agent_mm, agent_noise])
    stock_tnt.sod()
    stock_tnt.add_orders([buy_order_101_tnt])
    stock_tnt.step(1)
    sell_order_99_tnt.time = 2
    stock_tnt.add_orders([sell_order_99_tnt])
    new_orders_matched = stock_tnt.step(2)

    for matched_order in new_orders_matched:
        stock_tnt.record_trade(matched_order=matched_order)

    assert agent_noise.cash == Price(- 1010.00)
    assert agent_noise.agent_id == buy_order_101_tnt.agent_id
    assert agent_noise.position.get(stock_tnt.asset_id) == 10, "Inventory should be 10 - equal to the order volume"
    assert agent_mm.cash == Price(1010.00)
    assert agent_mm.agent_id == sell_order_99_tnt.agent_id
    assert agent_mm.position.get(stock_tnt.asset_id) == -10, "Inventory should be -10 - equal to the order volume but negative"
    # TODO: inspect the security stats, too



def test_cf_2(agent_noise: NoiseAgent,
              agent_mm: Agent,
              stock_tnt: Security):
    assert 1 == 1
