try:
    from _pytest._code import Source
except (ModuleNotFoundError, ImportError):  # pytest < 7.2
    from py.code import Source

__all__ = ["assert_outcomes", "Source"]


def assert_outcomes(result, **expected):
    """Assert that the test outcomes match what is expected."""
    outcomes = result.parseoutcomes()

    for key in 'seconds', 'warning', 'warnings':
        if key in outcomes:
            del outcomes[key]

    assert outcomes == expected
