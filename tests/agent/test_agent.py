import pytest

from marketsim.agent import (Agent, NoiseAgent, HBLAgent, MMZOHAgent, MomentumAgent, OptionMMZOHAgent, SpoofingAgent,
        WashTradingAgent, ZIAgentNotInformed)


#######   testing functions   #######


# [NoiseAgent, HBLAgent, MMZOHAgent, MomentumAgent, OptionMMZOHAgent, SpoofingAgent,
#         WashTradingAgent, ZIAgentNotInformed])
# def test_create_agent(stock, repository):
#     agent = (markets=[stock], repository=repository)
#
#     assert agent is not None


def test_create_agent_noise(stock, repository):
    agent = NoiseAgent(markets=[stock], repository=repository)

    assert agent is not None

def test_create_agent_hbl(stock, repository):
    agent = HBLAgent(markets=[stock], repository=repository)

    assert agent is not None

def test_create_agent_mm(stock, repository):
    agent = MMZOHAgent(markets=[stock], repository=repository)

    assert agent is not None

def test_create_agent_momentum(stock, repository):
    agent = MomentumAgent(markets=[stock], repository=repository)

    assert agent is not None

def test_create_agent_option_mm(stock, repository):
    agent = OptionMMZOHAgent(markets=[stock], repository=repository)

    assert agent is not None

def test_create_agent_spoof(stock, repository):
    agent = SpoofingAgent(markets=[stock], repository=repository)

    assert agent is not None

def test_create_agent_wash(stock, repository):
    agent = WashTradingAgent(markets=[stock], repository=repository)

    assert agent is not None

def test_create_agent_zi(stock, repository):
    agent = ZIAgentNotInformed(markets=[stock], repository=repository)

    assert agent is not None
