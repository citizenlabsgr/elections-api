import pytest


class Anything:
    def __eq__(self, other):
        return True


@pytest.fixture(scope='session')
def anything():
    return Anything()
