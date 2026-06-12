"""Test fixtures passed as describe block arguments (issue #38)"""


def test_module_fixture_as_describe_arg(pytester):
    pytester.makepyfile(
        """
        import pytest

        @pytest.fixture
        def thing():
            return 42

        def describe_something(thing):
            def thing_is_42():
                assert thing == 42

            def thing_is_not_43():
                assert thing != 43
        """
    )

    result = pytester.runpytest()
    result.assert_outcomes(passed=2)


def test_describe_arg_used_in_nested_block(pytester):
    pytester.makepyfile(
        """
        import pytest

        @pytest.fixture
        def thing():
            return 42

        def describe_something(thing):
            def describe_nested():
                def thing_is_42():
                    assert thing == 42
        """
    )

    result = pytester.runpytest()
    result.assert_outcomes(passed=1)


def test_local_fixture_as_nested_describe_arg(pytester):
    pytester.makepyfile(
        """
        import pytest

        def describe_something():
            @pytest.fixture
            def thing():
                return 42

            def describe_nested(thing):
                def thing_is_42():
                    assert thing == 42
        """
    )

    result = pytester.runpytest()
    result.assert_outcomes(passed=1)


def test_parametrized_fixture_as_describe_arg(pytester):
    pytester.makepyfile(
        """
        import pytest

        @pytest.fixture(params=[1, 2, 3])
        def number(request):
            return request.param

        def describe_something(number):
            def number_is_positive():
                assert number > 0
        """
    )

    result = pytester.runpytest()
    result.assert_outcomes(passed=3)


def test_mix_describe_args_and_test_args(pytester):
    pytester.makepyfile(
        """
        import pytest

        @pytest.fixture
        def user():
            return "alice"

        @pytest.fixture
        def book():
            return "moby dick"

        def describe_create_book(user):
            def with_book(book):
                assert user == "alice"
                assert book == "moby dick"
        """
    )

    result = pytester.runpytest()
    result.assert_outcomes(passed=1)


def test_parametrize_mark_inside_describe_with_args(pytester):
    pytester.makepyfile(
        """
        import pytest

        @pytest.fixture
        def thing():
            return 42

        def describe_something(thing):
            @pytest.mark.parametrize("offset", [1, 2])
            def thing_plus_offset(offset):
                assert thing + offset > 42
        """
    )

    result = pytester.runpytest()
    result.assert_outcomes(passed=2)


def test_unused_describe_arg_is_still_requested(pytester):
    pytester.makepyfile(
        """
        import pytest

        added = []

        @pytest.fixture
        def effect():
            added.append(1)

        def describe_something(effect):
            def effect_happened():
                assert added == [1]
        """
    )

    result = pytester.runpytest()
    result.assert_outcomes(passed=1)


def test_missing_fixture_for_describe_arg(pytester):
    pytester.makepyfile(
        """
        def describe_something(does_not_exist):
            def some_test():
                pass
        """
    )

    result = pytester.runpytest()
    result.assert_outcomes(errors=1)
    result.stdout.fnmatch_lines(["*fixture 'does_not_exist' not found*"])


def test_placeholder_is_restored_between_tests(pytester):
    pytester.makepyfile(
        """
        import pytest

        @pytest.fixture(params=["a", "b"])
        def letter(request):
            return request.param

        def describe_something(letter):
            def letter_is_valid():
                assert letter in ("a", "b")

            def letter_is_short():
                assert len(letter) == 1
        """
    )

    result = pytester.runpytest()
    result.assert_outcomes(passed=4)
