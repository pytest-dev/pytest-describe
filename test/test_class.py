"""Test that classes are ignored"""


def test_skip_classes(testdir):
    testdir.makepyfile(
        """
        def describe_something():
            def fn():
                assert True
            class cls:
                def __call__(self):
                    assert True
        """)

    result = testdir.runpytest()
    result.assert_outcomes(passed=1)
