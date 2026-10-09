import pytest

from marketsim.database.connectors.duckdb_storage import Repository
from marketsim.market import Security, Option, Price
from tests.conftest import repository, option_tnt_call
from marketsim.agent import Agent, NoiseAgent


@pytest.fixture
def derivatives_config1(stock: Security):
    config1 = { "underlying": stock,
                "strike": Price(90),
                "expiration": 30,
                "option_side": "CALL",
                "option_type": "European",
                }
    return config1

@pytest.fixture
def config_tnt_call(stock: Security):
    config1 = {
                "strike": Price(90),
                "expiration": 30,
                "option_side": "CALL",
                "option_type": "European",
                }
    return config1

@pytest.fixture
def config_tnt_put(stock: Security):
    config1 = {
                "strike": Price(90),
                "expiration": 30,
                "option_side": "PUT",
                "option_type": "European",
                }
    return config1



@pytest.fixture
def option_call_before_expiration_itm(stock_tnt: Security,
                                      config_tnt_call: dict,
                                      repository: Repository) -> Option:
    opt = Option(derivatives_config=config_tnt_call,
                 short_name="CALL before expiration ITM",
                 repository=repository,
                 underlying=stock_tnt)
    opt.sod()
    return opt

@pytest.fixture
def option_call_at_expiration_itm(stock_tnt: Security,
                                      config_tnt_call: dict,
                                      repository: Repository) -> Option:
    config_tnt_call["expiration"] = 0
    opt = Option(derivatives_config=config_tnt_call,
                 short_name="CALL at expiration ITM",
                 repository=repository,
                 underlying=stock_tnt)
    opt.sod()
    return opt


@pytest.fixture
def option_put_before_expiration_itm(stock_tnt: Security,
                                      config_tnt_put: dict,
                                      repository: Repository) -> Option:
    opt = Option(derivatives_config=config_tnt_put,
                 short_name="PUT before expiration ITM",
                 repository=repository,
                 underlying=stock_tnt)
    opt.sod()
    return opt

@pytest.fixture
def option_put_at_expiration_itm(stock_tnt: Security,
                                      config_tnt_put: dict,
                                      repository: Repository) -> Option:
    config_tnt_put["expiration"] = 0
    config_tnt_put["strike"] = Price(170.00)
    opt = Option(derivatives_config=config_tnt_put,
                 short_name="PUT at expiration ITM K: 170",
                 repository=repository,
                 underlying=stock_tnt)
    opt.sod()
    return opt


@pytest.fixture
def option_call_before_expiration_atm(stock_tnt: Security,
                                      config_tnt_call: dict,
                                      repository: Repository) -> Option:
    config_tnt_call["strike"] = Price(167)
    opt = Option(derivatives_config=config_tnt_call,
                 short_name="CALL before expiration ITM",
                 repository=repository,
                 underlying=stock_tnt)
    opt.sod()
    return opt

@pytest.fixture
def option_call_at_expiration_atm(stock_tnt: Security,
                                      config_tnt_call: dict,
                                      repository: Repository) -> Option:
    config_tnt_call["expiration"] = 0
    config_tnt_call["strike"] = Price(167)
    opt = Option(derivatives_config=config_tnt_call,
                 short_name="CALL at expiration ITM",
                 repository=repository,
                 underlying=stock_tnt)
    opt.sod()
    return opt


@pytest.fixture
def option_put_before_expiration_atm(stock_tnt: Security,
                                      config_tnt_put: dict,
                                      repository: Repository) -> Option:
    config_tnt_put["strike"] = Price(167)
    opt = Option(derivatives_config=config_tnt_put,
                 short_name="PUT before expiration ATM",
                 repository=repository,
                 underlying=stock_tnt)
    opt.sod()
    return opt

@pytest.fixture
def option_put_at_expiration_atm(stock_tnt: Security,
                                      config_tnt_put: dict,
                                      repository: Repository) -> Option:
    config_tnt_put["expiration"] = 0
    config_tnt_put["strike"] = Price(167)
    opt = Option(derivatives_config=config_tnt_put,
                 short_name="PUT at expiration ATM",
                 repository=repository,
                 underlying=stock_tnt)
    opt.sod()
    return opt


@pytest.fixture
def option_call_before_expiration_otm(stock_tnt: Security,
                                      config_tnt_call: dict,
                                      repository: Repository) -> Option:
    config_tnt_call["strike"] = Price(120)
    opt = Option(derivatives_config=config_tnt_call,
                 short_name="CALL before expiration OTM",
                 repository=repository,
                 underlying=stock_tnt)
    opt.sod()
    return opt

@pytest.fixture
def option_call_at_expiration_otm(stock_tnt: Security,
                                      config_tnt_call: dict,
                                      repository: Repository) -> Option:
    config_tnt_call["expiration"] = 0
    config_tnt_call["strike"] = Price(180)
    opt = Option(derivatives_config=config_tnt_call,
                 short_name="CALL at expiration OTM",
                 repository=repository,
                 underlying=stock_tnt)
    opt.sod()
    return opt


@pytest.fixture
def option_put_before_expiration_otm(stock_tnt: Security,
                                      config_tnt_put: dict,
                                      repository: Repository) -> Option:
    config_tnt_put["strike"] = Price(168)
    opt = Option(derivatives_config=config_tnt_put,
                 short_name="PUT before expiration OTM",
                 repository=repository,
                 underlying=stock_tnt)
    opt.sod()
    return opt

@pytest.fixture
def option_put_at_expiration_otm(stock_tnt: Security,
                                      config_tnt_put: dict,
                                      repository: Repository) -> Option:
    config_tnt_put["expiration"] = 0
    config_tnt_put["strike"] = Price(165)
    opt = Option(derivatives_config=config_tnt_put,
                 short_name="PUT at expiration OTM",
                 repository=repository,
                 underlying=stock_tnt)
    opt.sod()
    return opt


### agents with option in portfolio:

@pytest.fixture
def agent_long_call_option_expiration_day(stock_tnt: Security,
                                          stock_mit: Security,
                                          option_call_at_expiration_itm: Option,
                                          repository: Repository):
    agent =  NoiseAgent(markets=[stock_tnt, stock_mit, option_call_at_expiration_itm], repository=repository)
    option_call_at_expiration_itm.add_agents([agent])
    agent.position[option_call_at_expiration_itm.asset_id] = 10

    return agent


@pytest.fixture
def agent_long_put_option_expiration_day(stock_tnt: Security,
                                          stock_mit: Security,
                                          option_put_at_expiration_itm: Option,
                                          repository: Repository):
    agent =  NoiseAgent(markets=[stock_tnt, stock_mit, option_put_at_expiration_itm], repository=repository)
    option_put_at_expiration_itm.add_agents([agent])
    agent.position[option_put_at_expiration_itm.asset_id] = 10

    return agent

@pytest.fixture
def agent_long_call_option_expiration_day_otm(stock_tnt: Security,
                                          stock_mit: Security,
                                          option_call_at_expiration_otm: Option,
                                          repository: Repository):
    agent =  NoiseAgent(markets=[stock_tnt, stock_mit, option_call_at_expiration_otm], repository=repository)
    option_call_at_expiration_otm.add_agents([agent])
    agent.position[option_call_at_expiration_otm.asset_id] = 10

    return agent


@pytest.fixture
def agent_long_put_option_expiration_day_otm(stock_tnt: Security,
                                          stock_mit: Security,
                                          option_put_at_expiration_otm: Option,
                                          repository: Repository):
    agent =  NoiseAgent(markets=[stock_tnt, stock_mit, option_put_at_expiration_otm], repository=repository)
    option_put_at_expiration_otm.add_agents([agent])
    agent.position[option_put_at_expiration_otm.asset_id] = 10

    return agent


# for sod testing after option expire:

@pytest.fixture
def agent_after_expiry_call(agent_long_call_option_expiration_day: Agent,
                              option_call_at_expiration_itm: Option):
    option_call_at_expiration_itm.eod()
    agent_long_call_option_expiration_day.eod()

    return agent_long_call_option_expiration_day

@pytest.fixture
def agent_after_expiry_put(agent_long_put_option_expiration_day: Agent,
                              option_put_at_expiration_itm: Option):
    option_put_at_expiration_itm.eod()
    agent_long_put_option_expiration_day.eod()

    return agent_long_put_option_expiration_day

@pytest.fixture
def agent_after_expiry_call_otm(agent_long_call_option_expiration_day_otm: Agent,
                              option_call_at_expiration_otm: Option):
    option_call_at_expiration_otm.eod()
    agent_long_call_option_expiration_day_otm.eod()

    return agent_long_call_option_expiration_day_otm

@pytest.fixture
def agent_after_expiry_put_otm(agent_long_put_option_expiration_day_otm: Agent,
                              option_put_at_expiration_otm: Option):
    option_put_at_expiration_otm.eod()
    agent_long_put_option_expiration_day_otm.eod()

    return agent_long_put_option_expiration_day_otm
