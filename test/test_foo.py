import pytest


@pytest.fixture
def thing():
    return 23


def test_foo(thing):
    assert thing == 23


def describe_a_nested_test_suite():

    def passes():
        pass

    @pytest.mark.xfail
    def fails():
        assert False

    @pytest.fixture
    def thang():
        return 12

    def describe_a_nested_suite_with_local_fixture():

        @pytest.fixture
        def thang():
            return 42

        @pytest.fixture
        def baba():
            pass

        def thang_is_42(thang):
            assert thang == 42

        def uses_both_thing_and_thang(thing, thang):
            assert thing < thang

    def describe_another_nested_suite():

        @pytest.mark.xfail
        def fails():
            assert False

        @pytest.mark.parametrize('foo', (1, 2, 3))
        def isint(foo):
            assert foo == int(foo)

        def _does_not_run():
            assert False

        def thang_is_12(thang):
            assert thang == 12

    def thang_is_12(thang):
        assert thang == 12


@pytest.mark.xfail
def test_thang(thang):
    assert thang
