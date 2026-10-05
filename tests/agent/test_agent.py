import pytest

from marketsim.agent import Agent, NoiseAgent


#######   testing functions   #######


def test_create_agent(stock, repository):
    agent = NoiseAgent(markets=[stock], repository=repository)


    assert agent is not None
