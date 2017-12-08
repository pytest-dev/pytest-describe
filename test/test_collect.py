import py
from util import assert_outcomes

pytest_plugins = 'pytester'


def test_collect(testdir):
    a_dir = testdir.mkpydir('a_dir')
    a_dir.join('test_a.py').write(py.code.Source("""
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
    """))

    result = testdir.runpytest('--collectonly')
    expected_lines = [
        "collected 4 items",
        "  <DescribeBlock 'describe_something'>",
        "    <Function 'is_foo'>",
        "    <Function 'can_bar'>",
        "  <DescribeBlock 'describe_something_else'>",
        "    <DescribeBlock 'describe_nested'>",
        "      <Function 'a_test'>",
        "  <Function 'test_something'>",
    ]
    for line in expected_lines:
        assert line in result.outlines


def test_describe_evaluated_once(testdir):
    a_dir = testdir.mkpydir('a_dir')
    a_dir.join('test_something.py').write(py.code.Source("""
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
    """))

    result = testdir.runpytest('-v')
    assert_outcomes(result, passed=3)
