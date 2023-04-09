"""Test with fixtures"""


def test_can_access_local_fixture(testdir):
    testdir.makepyfile(
        """
        import pytest

        def describe_something():
            @pytest.fixture
            def thing():
                return 42

            def thing_is_42(thing):
                assert thing == 42
        """)

    result = testdir.runpytest()
    result.assert_outcomes(passed=1)


def test_can_access_fixture_from_nested_scope(testdir):
    testdir.makepyfile(
        """
        import pytest

        def describe_something():
            @pytest.fixture
            def thing():
                return 42

            def describe_a_nested_scope():
                def thing_is_42(thing):
                    assert thing == 42
        """)

    result = testdir.runpytest()
    result.assert_outcomes(passed=1)


def test_local_fixture_overrides(testdir):
    testdir.makepyfile(
        """
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
        """)

    result = testdir.runpytest()
    result.assert_outcomes(passed=2)
