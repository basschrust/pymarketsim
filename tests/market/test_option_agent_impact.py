import pytest

from marketsim.agent import Agent
from marketsim.market import Option, Price

######## test functions  ######


def test_cf_after_expiry_call(agent_long_call_option_expiration_day: Agent,
                              option_call_at_expiration_itm: Option):
    option_call_at_expiration_itm.eod()
    agent_long_call_option_expiration_day.eod()

    assert agent_long_call_option_expiration_day.position[option_call_at_expiration_itm.asset_id] == 0, "Should be 0"
    assert option_call_at_expiration_itm.current_day == 1, "Date should be rolled"
    assert agent_long_call_option_expiration_day.current_day == 1, "Date should be rolled"
    assert agent_long_call_option_expiration_day.cash == Price(770.00), "Cash should be 10*77 position * premium"
    assert agent_long_call_option_expiration_day.portfolio_value == Price(770.00), "Portolio value equal to cash"


