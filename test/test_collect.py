"""Test collection of test functions"""


def test_collect_only(pytester):
    pytester.makepyfile(
        """
        def describe_something():
            def is_foo():
                pass
            def can_bar():
                pass
            def _not_a_test():
                pass
        def describe_something_else():
            def describe_nested():
                def a_test():
                    pass
        def foo_not_collected():
            pass
        def test_something():
            pass
        """
    )

    result = pytester.runpytest("--collectonly")
    result.assert_outcomes()

    result.stdout.fnmatch_lines(
        [
            "*collected 4 items*",
            "*<Module test_collect_only.py>",
            "*<DescribeBlock 'describe_something'>",
            "*<Function is_foo>",
            "*<Function can_bar>",
            "*<DescribeBlock 'describe_something_else'>",
            "*<DescribeBlock 'describe_nested'>",
            "*<Function a_test>",
            "*<Function test_something>",
        ]
    )


def test_describe_evaluated_once(pytester):
    pytester.makepyfile(
        """
        count = 0
        def describe_is_evaluated_only_once():
            global count
            count += 1
            def one():
                assert count == 1
            def two():
                assert count == 1
            def describe_nested():
                def three():
                    assert count == 1
    """
    )

    result = pytester.runpytest("-v")
    result.assert_outcomes(passed=3)
