from util import assert_outcomes, Source

pytest_plugins = 'pytester'


def test_can_access_local_fixture(testdir):
    a_dir = testdir.mkpydir('a_dir')
    a_dir.join('test_a.py').write(Source("""
        import pytest

        def describe_something():
            @pytest.fixture
            def thing():
                return 42

            def thing_is_42(thing):
                assert thing == 42
    """))

    result = testdir.runpytest()
    assert_outcomes(result, passed=1)


def test_can_access_fixture_from_nested_scope(testdir):
    a_dir = testdir.mkpydir('a_dir')
    a_dir.join('test_a.py').write(Source("""
        import pytest

        def describe_something():
            @pytest.fixture
            def thing():
                return 42

            def describe_a_nested_scope():
                def thing_is_42(thing):
                    assert thing == 42
    """))

    result = testdir.runpytest()
    assert_outcomes(result, passed=1)


def test_local_fixture_overrides(testdir):
    a_dir = testdir.mkpydir('a_dir')
    a_dir.join('test_a.py').write(Source("""
        import pytest

        @pytest.fixture
        def thing():
            return 12

        def describe_something():
            def describe_a_nested_scope():
                @pytest.fixture
                def thing():
                    return 42

                def thing_is_42(thing):
                    assert thing == 42

            def thing_is_12(thing):
                assert thing == 12
    """))

    result = testdir.runpytest()
    assert_outcomes(result, passed=2)
