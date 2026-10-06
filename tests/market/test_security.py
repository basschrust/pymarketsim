import pytest

from marketsim.market import Price, Security


############  test functions  ##################

def test_create_security(repository):
    security = Security(repository=repository)

    assert security is not None

def test_sod(security: Security):
    security.current_time = 3
    security.sod()

    assert security.current_time == 3
    assert security.eod_status == "open"


