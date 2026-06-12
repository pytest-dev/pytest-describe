"""Test using docstrings as names for describe blocks"""


def test_docstrings_not_used_by_default(pytester):
    pytester.makepyfile(
        """
        def describe_wallet():
            '''a wallet'''

            def it_is_empty():
                pass
        """
    )

    result = pytester.runpytest("-v")

    result.assert_outcomes(passed=1)
    result.stdout.fnmatch_lines(["*::describe_wallet::it_is_empty PASSED*"])


def test_docstrings_used_as_names_when_enabled(pytester):
    pytester.makeini(
        """
        [pytest]
        describe_docstrings = true
        """
    )
    pytester.makepyfile(
        """
        def describe_wallet():
            '''a wallet'''

            def describe_when_empty():
                '''when it is empty

                This second line should not appear in the name.
                '''

                def it_has_no_balance():
                    pass

            def describe_without_docstring():

                def it_keeps_the_function_name():
                    pass
        """
    )

    result = pytester.runpytest("-v")

    result.assert_outcomes(passed=2)
    result.stdout.fnmatch_lines(
        [
            "*::a wallet::when it is empty::it_has_no_balance PASSED*",
            (
                "*::a wallet::describe_without_docstring"
                "::it_keeps_the_function_name PASSED*"
            ),
        ]
    )


def test_docstrings_used_for_shared_behaviors(pytester):
    pytester.makeini(
        """
        [pytest]
        describe_docstrings = true
        """
    )
    pytester.makepyfile(
        """
        from pytest import fixture
        from pytest_describe import behaves_like

        def a_duck():

            def describe_sound():
                '''the sound it makes'''

                def it_quacks(sound):
                    assert sound == 'quack'

        @behaves_like(a_duck)
        def describe_something_that_quacks():
            '''something that quacks'''

            @fixture
            def sound():
                return 'quack'
        """
    )

    result = pytester.runpytest("-v")

    result.assert_outcomes(passed=1)
    result.stdout.fnmatch_lines(
        [
            ("*::something that quacks::the sound it makes::it_quacks PASSED*"),
        ]
    )


def test_selection_by_docstring_name(pytester):
    pytester.makeini(
        """
        [pytest]
        describe_docstrings = true
        """
    )
    pytester.makepyfile(
        """
        def describe_wallet():
            '''a wallet'''

            def it_is_selected():
                pass

        def describe_purse():

            def it_is_not_selected():
                pass
        """
    )

    result = pytester.runpytest("-k", "wallet")

    result.assert_outcomes(passed=1, deselected=1)
