import pytest

from marketsim.market import Price, Security


############  test functions  ##################

def test_create_security(repository):
    security = Security(repository=repository)

    assert security is not None

