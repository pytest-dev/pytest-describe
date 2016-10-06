import py
from util import assert_outcomes

pytest_plugins = 'pytester'


def test_shared_behavior(testdir):
    a_dir = testdir.mkpydir('a_dir')
    a_dir.join('test_something.py').write(py.code.Source("""
        from pytest import fixture
        from pytest_describe import behaves_like

        def a_duck():
            def it_quacks(sound):
                assert sound == "quack"

        @behaves_like(a_duck)
        def describe_something_that_quacks():
            @fixture
            def sound():
                return "quack"

        @behaves_like(a_duck)
        def describe_something_that_barks():
            @fixture
            def sound():
                return "bark"
    """))

    result = testdir.runpytest()
    assert_outcomes(result, failed=1, passed=1)
