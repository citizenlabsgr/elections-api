from datetime import timedelta

import pytest

from elections import helpers


class Anything:
    def __eq__(self, other):
        return True


@pytest.fixture(scope='session')
def anything():
    return Anything()


@pytest.fixture(scope='session', autouse=True)
def requests_cache():
    helpers.enable_requests_cache(timedelta(hours=12))
