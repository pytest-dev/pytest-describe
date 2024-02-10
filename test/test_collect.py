"""Test collection of test functions"""

from textwrap import dedent


def test_collect_only(testdir):
    testdir.makepyfile(
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
        """)

    result = testdir.runpytest('--collectonly')
    result.assert_outcomes()

    output = '\n'.join(line.lstrip() for line in result.outlines)
    assert "collected 4 items" in output
    assert dedent("""
        <Module test_collect_only.py>
        <DescribeBlock 'describe_something'>
        <Function is_foo>
        <Function can_bar>
        <DescribeBlock 'describe_something_else'>
        <DescribeBlock 'describe_nested'>
        <Function a_test>
        <Function test_something>
        """) in output


def test_describe_evaluated_once(testdir):
    testdir.makepyfile(
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
    """)

    result = testdir.runpytest('-v')
    result.assert_outcomes(passed=3)
