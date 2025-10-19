"""Global fixtures for testing the plugin"""

import pytest

# Ensure the internal pytester plugin is loaded where available
pytest_plugins = ["pytester"]

# Backport pytester fixture for pytest < 6.2
if getattr(pytest, "version_tuple", (6, 0)) < (6, 2):

    @pytest.fixture
    def pytester(testdir):  # pragma: no cover
        return testdir
