from datetime import timedelta

import pytest
import requests_cache


class Anything:
    def __eq__(self, other):
        return True


@pytest.fixture(scope='session')
def anything():
    return Anything()


@pytest.fixture(scope='session', autouse=True)
def cache_requests():
    requests_cache.install_cache(expire_after=timedelta(hours=12))
