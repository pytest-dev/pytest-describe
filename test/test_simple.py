"""Test simple execution"""


def test_can_pass(pytester):
    pytester.makepyfile(
        """
        def describe_something():
            def passes():
                assert True
            def describe_nested():
                def passes_too():
                    assert True
        """
    )

    result = pytester.runpytest()
    result.assert_outcomes(passed=2)


def test_can_fail(pytester):
    pytester.makepyfile(
        """
        def describe_something():
            def fails():
                assert False
            def describe_nested():
                def fails_too():
                    assert False
        """
    )

    result = pytester.runpytest()
    result.assert_outcomes(failed=2)


def test_can_fail_and_pass(pytester):
    pytester.makepyfile(
        """
        def describe_something():
            def describe_nested_ok():
                def passes():
                    assert True
            def describe_nested_bad():
                def fails():
                    assert False
        """
    )

    result = pytester.runpytest()
    result.assert_outcomes(passed=1, failed=1)
