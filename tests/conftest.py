from datetime import timedelta

import log
import pytest
import requests_cache


class Anything:
    def __eq__(self, other):
        return True


def pytest_configure(config):
    """Disable verbose output when running tests."""
    log.init(debug=True)
    log.silence('elections.defaults', allow_warning=True)
    log.silence('elections.helpers', allow_info=True)
    log.silence('asyncio', 'factory', 'faker', 'urllib3', 'vcr')

    terminal = config.pluginmanager.getplugin("terminal")
    terminal.TerminalReporter.showfspath = False

    requests_cache.install_cache(expire_after=timedelta(hours=12))


@pytest.fixture(scope='session')
def anything():
    return Anything()
