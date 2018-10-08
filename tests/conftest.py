import logging
import os
import sys
from datetime import timedelta

import pytest
import requests_cache


class RelativePathFilter(logging.Filter):
    """Adds '%(relpath)s' as a 'LogRecord' attribute."""

    def filter(self, record):
        pathname = record.pathname
        record.relpath = None
        abs_sys_paths = [os.path.abspath(p) for p in sys.path]
        for path in sorted(abs_sys_paths, key=len, reverse=True):
            if not path.endswith(os.sep):
                path += os.sep
            if pathname.startswith(path):
                record.relpath = os.path.relpath(pathname, path)
                break
        return True


class Anything:
    def __eq__(self, other):
        return True


@pytest.fixture(scope='session', autouse=True)
def relpath_logging():
    # TODO: Determine why this call isn't enough
    # import log
    # log.helpers.add_custom_filters()
    for handler in logging.root.handlers:
        handler.addFilter(RelativePathFilter())


@pytest.fixture(scope='session')
def anything():
    return Anything()


@pytest.fixture(scope='session', autouse=True)
def cache_requests():
    requests_cache.install_cache(expire_after=timedelta(hours=12))
