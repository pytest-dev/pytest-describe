import py
from util import assert_outcomes

from pytest_describe.plugin import InjectFixture, accesses_arguments


def test_accesses_arguments_params():
    def f(x):
        x

    assert accesses_arguments(f)


def test_accesses_arguments_closure():
    def outer(x):
        def inner():
            x
        return inner
    inner = outer(1)
    inner._parent_fixture_args = {InjectFixture('x')}

    assert not accesses_arguments(outer)
    assert accesses_arguments(inner)


def test_accesses_arguments_locals():
    def outer():
        x = 1
        x
        print(x)

    assert not accesses_arguments(outer)


def test_accesses_arguments_outer_locals():
    def outer():
        x = 1
        x
        def inner():
            x
        return inner

    assert not accesses_arguments(outer)
    assert not accesses_arguments(outer())


def test_inject_fixtures(testdir):
    a_dir = testdir.mkpydir('a_dir')
    a_dir.join('test_a.py').write(py.code.Source("""
        import pytest

        @pytest.fixture
        def thing():
            return 42

        def describe_something(thing):

            def thing_is_not_43():
                assert thing != 43

            def describe_nested_block():

                def thing_is_42():
                    assert thing == 42
    """))

    result = testdir.runpytest()
    assert_outcomes(result, passed=2)
