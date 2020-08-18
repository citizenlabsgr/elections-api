import log


def pytest_configure(config):
    """Disable verbose output when running tests."""
    log.init(debug=True)
    log.silence('elections.defaults', 'parse', 'pomace', allow_warning=True)
    log.silence('elections.helpers', allow_info=True)
    log.silence('asyncio', 'factory', 'faker', 'selenium', 'urllib3', 'vcr')

    terminal = config.pluginmanager.getplugin("terminal")
    terminal.TerminalReporter.showfspath = False
