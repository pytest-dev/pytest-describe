"""Test fixtures passed as describe block arguments (issue #38)"""

import pytest

from pytest_describe.plugin import DescribeArgument, DescribeArgumentError


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


def test_using_describe_arg_in_describe_body_raises(pytester):
    pytester.makepyfile(
        """
        import pytest

        @pytest.fixture
        def thing():
            return 42

        def describe_something(thing):
            doubled = thing + thing

            def some_test():
                assert doubled == 84
        """
    )

    result = pytester.runpytest()
    result.assert_outcomes(errors=1)
    result.stdout.fnmatch_lines(
        ["*The argument 'thing' is a placeholder for a fixture*"]
    )


def test_describe_arg_with_default_is_not_a_fixture(pytester):
    pytester.makepyfile(
        """
        def describe_something(thing=42):
            def thing_is_42():
                assert thing == 42
        """
    )

    result = pytester.runpytest()
    result.assert_outcomes(passed=1)


def test_keyword_only_describe_arg(pytester):
    pytester.makepyfile(
        """
        import pytest

        @pytest.fixture
        def thing():
            return 42

        def describe_something(*, thing):
            def thing_is_42():
                assert thing == 42
        """
    )

    result = pytester.runpytest()
    result.assert_outcomes(passed=1)


def test_shared_behavior_with_args(pytester):
    pytester.makepyfile(
        """
        import pytest
        from pytest_describe import behaves_like

        def a_duck(sound):
            def it_quacks():
                assert sound == "quack"

        @behaves_like(a_duck)
        def describe_something_that_quacks():
            @pytest.fixture
            def sound():
                return "quack"

        @behaves_like(a_duck)
        def describe_something_that_barks():
            @pytest.fixture
            def sound():
                return "bark"
        """
    )

    result = pytester.runpytest()
    result.assert_outcomes(failed=1, passed=1)


def test_transitive_parametrized_dependency(pytester):
    pytester.makepyfile(
        """
        import pytest

        @pytest.fixture(params=[1, 2, 3])
        def number(request):
            return request.param

        @pytest.fixture
        def double(number):
            return 2 * number

        def describe_something(double):
            def double_is_even():
                assert double % 2 == 0
        """
    )

    result = pytester.runpytest()
    result.assert_outcomes(passed=3)


def test_same_fixture_as_describe_and_test_arg(pytester):
    pytester.makepyfile(
        """
        import pytest

        @pytest.fixture
        def thing():
            return 42

        def describe_something(thing):
            def thing_is_42(thing):
                assert thing == 42
        """
    )

    result = pytester.runpytest()
    result.assert_outcomes(passed=1)


def test_local_fixture_uses_describe_arg(pytester):
    pytester.makepyfile(
        """
        import pytest

        @pytest.fixture
        def number():
            return 21

        def describe_something(number):
            @pytest.fixture
            def double():
                return 2 * number

            def double_is_42(double):
                assert double == 42
        """
    )

    result = pytester.runpytest()
    result.assert_outcomes(passed=1)


def test_multiple_describe_args(pytester):
    pytester.makepyfile(
        """
        import pytest

        @pytest.fixture
        def first():
            return 1

        @pytest.fixture
        def second():
            return 2

        def describe_something(first, second):
            def sum_is_3():
                assert first + second == 3
        """
    )

    result = pytester.runpytest()
    result.assert_outcomes(passed=1)


def test_missing_fixture_referenced_in_test(pytester):
    pytester.makepyfile(
        """
        def describe_something(does_not_exist):
            def some_test():
                assert does_not_exist
        """
    )

    result = pytester.runpytest()
    result.assert_outcomes(errors=1)
    result.stdout.fnmatch_lines(["*fixture 'does_not_exist' not found*"])


def test_shared_behavior_arg_same_as_describe_arg(pytester):
    pytester.makepyfile(
        """
        import pytest
        from pytest_describe import behaves_like

        def a_duck(sound):
            def it_quacks():
                assert sound == "quack"

        @behaves_like(a_duck)
        def describe_quacking(sound):
            def it_still_quacks():
                assert sound == "quack"

        @pytest.fixture
        def sound():
            return "quack"
        """
    )

    result = pytester.runpytest()
    result.assert_outcomes(passed=2)


def test_placeholder_repr_and_misuse_message():
    placeholder = DescribeArgument("thing")
    assert repr(placeholder) == (
        "<describe argument 'thing' (the fixture is only available inside tests)>"
    )
    with pytest.raises(DescribeArgumentError, match="placeholder"):
        _ = placeholder.some_attribute
    with pytest.raises(DescribeArgumentError, match="cannot be used"):
        placeholder()


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
