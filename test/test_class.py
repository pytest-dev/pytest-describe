"""Test that classes are ignored"""


def test_skip_classes(pytester):
    pytester.makepyfile(
        """
        def describe_something():
            def fn():
                assert True
            class cls:
                def __call__(self):
                    assert True
        """
    )

    result = pytester.runpytest()
    result.assert_outcomes(passed=1)
