"""Test shared behaviors"""


def test_shared_behaviors(pytester):
    pytester.makepyfile(
        """
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
        """
    )

    result = pytester.runpytest()
    result.assert_outcomes(failed=1, passed=1)


def test_multiple_shared_behaviors(pytester):
    pytester.makepyfile(
        """
        from pytest import fixture
        from pytest_describe import behaves_like

        def a_duck():
            def it_quacks(sound):
                assert sound == "quack"

        def a_bird():
            def it_flies(medium):
                assert medium == "air"

        def describe_birds():
            @fixture
            def medium():
                return "air"

            @behaves_like(a_duck, a_bird)
            def describe_something_that_quacks():
                @fixture
                def sound():
                    return "quack"

            @behaves_like(a_duck, a_bird)
            def describe_something_that_barks():
                @fixture
                def sound():
                    return "bark"
        """
    )

    result = pytester.runpytest()
    result.assert_outcomes(failed=1, passed=3)


def test_fixture(pytester):
    pytester.makepyfile(
        """
        from pytest import fixture
        from pytest_describe import behaves_like

        def a_duck():
            @fixture
            def sound():
                return "quack"

            def it_quacks(sound):
                assert sound == "quack"

        @behaves_like(a_duck)
        def describe_a_normal_duck():
            pass
        """
    )

    result = pytester.runpytest("-v")
    result.assert_outcomes(passed=1)


def test_override_fixture(pytester):
    pytester.makepyfile(
        """
        from pytest import fixture
        from pytest_describe import behaves_like

        def a_duck():
            @fixture
            def sound():
                return "quack"

            def it_quacks(sound):
                assert sound == "quack"

        @behaves_like(a_duck)
        def describe_something_that_barks():
            @fixture
            def sound():
                return "bark"
        """
    )

    result = pytester.runpytest("-v")
    result.assert_outcomes(failed=1)


def test_name_mangling(pytester):
    pytester.makepyfile(
        """
        from pytest import fixture
        from pytest_describe import behaves_like

        def thing():
            foo = 42
            def it_does_something():
                assert foo == 42

        @behaves_like(thing)
        def describe_something():
            foo = 4242
            def it_does_something():
                assert foo == 4242
        """
    )

    result = pytester.runpytest("-v")
    result.assert_outcomes(passed=2)


def test_nested_name_mangling(pytester):
    pytester.makepyfile(
        """
        from pytest import fixture
        from pytest_describe import behaves_like

        def thing():
            def it_does_something():
                pass
            def describe_thing():
                def it_does_something():
                    pass
                def describe_thing():
                    def it_does_something():
                        pass

        @behaves_like(thing)
        def describe_thing():
            def it_does_something():
                pass
            def describe_thing():
                def it_does_something():
                    pass
        """
    )

    result = pytester.runpytest("-v")
    result.assert_outcomes(passed=5)


def test_evaluated_once(pytester):
    pytester.makepyfile(
        """
        from pytest import fixture
        from pytest_describe import behaves_like

        count = 0
        def thing():
            global count
            count += 1
            def is_evaluated_once():
                assert count == 1

        @behaves_like(thing)
        def describe_something():
            pass
        @behaves_like(thing)
        def describe_something_else():
            pass
        """
    )

    result = pytester.runpytest("-v")
    result.assert_outcomes(passed=2)
