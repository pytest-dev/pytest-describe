"""Test metadata"""

import pytest_describe


def test_version_is_set():
    version = pytest_describe.__version__
    assert isinstance(version, str)
    assert "." in version
    assert not version.startswith("0")
    assert "unknown" not in version
