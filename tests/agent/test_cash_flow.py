import pytest

from marketsim.market import Security
from marketsim.agent import NoiseAgent, Agent
from tests.conftest import stock_tnt


@pytest.fixture



#####   test  functions ##########

def test_cf_1():
    assert 1 == 1


def test_cf_2(agent_noise: NoiseAgent,
              agent_mm: Agent,
              stock_tnt: Security):
    assert 1 == 1
