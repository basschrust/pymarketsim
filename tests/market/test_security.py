import pytest

from marketsim.market import Price, Security


############  test functions  ##################

def test_create_security(repository):
    security = Security(repository=repository)

    assert security is not None

def test_sod(security: Security):
    security.current_time = 3
    security.sod()

    assert security.current_time == 3 # TODO: reset time?
    assert security.eod_status == "open"


def test_eod_no_sod(security: Security):
    security.current_time = 3
    security.current_day = 5
    security.eod()

    assert security.current_time == 3, "Security during  should have the current time unchanged a"
    assert security.current_day == 5, "Security not started day doesn't roll date"
    assert security.eod_status == "closed"

# @pytest.mark.skip(reason="fill orders first")
def test_eod_after_sod(security: Security):
    security.current_day = 3
    security.sod()
    # yet fails as no trades and not filled
    security.eod()

    assert security.current_day == 4, "Security should have the date rolled"
    assert security.current_time == 0, "EoD resets the current time"
    assert security.eod_status == "closed"
