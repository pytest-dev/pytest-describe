"""Test mark decorator"""


def assert_outcomes(result, **kwargs):
    """Get all relevant outcomes"""
    assert {
        key: value
        for key, value in result.parseoutcomes().items()
        if key != 'seconds'
    } == kwargs  # pragma: no cover


def test_special_marks(testdir):
    testdir.makepyfile(
        """
        import pytest

        def describe_marks():
            @pytest.mark.xfail
            def xfails():
                assert False

            @pytest.mark.xfail
            def xpasses():
                pass

            @pytest.mark.skipif("0 < 1")
            def skipped():
                pass

            @pytest.mark.parametrize('foo', (1, 2, 3))
            def isint(foo):
                assert foo == int(foo)
        """)

    result = testdir.runpytest()
    result.assert_outcomes(passed=3, xfailed=1, xpassed=1, skipped=1)


def test_multiple_variables_parametrize(testdir):
    testdir.makepyfile(
        """
        import pytest

        def describe_marks():
            @pytest.mark.parametrize('foo,bar', [(1, 2), (3, 4)])
            def isint_str_names(foo, bar):
                assert foo == int(foo)
                assert bar == int(bar)

            @pytest.mark.parametrize(['foo', 'bar'], [(1, 2), (3, 4)])
            def isint_list_names(foo, bar):
                assert foo == int(foo)
                assert bar == int(bar)

            @pytest.mark.parametrize(('foo', 'bar'), [(1, 2), (3, 4)])
            def isint_tuple_names(foo, bar):
                assert foo == int(foo)
                assert bar == int(bar)
        """)

    result = testdir.runpytest()
    result.assert_outcomes(passed=6)


def test_cartesian_parametrize(testdir):
    testdir.makepyfile(
        """
        import pytest

        def describe_marks():

            @pytest.mark.parametrize('foo', (1, 2, 3))
            @pytest.mark.parametrize('bar', (1, 2, 3))
            def isint(foo, bar):
                assert foo == int(foo)
                assert bar == int(bar)
        """)

    result = testdir.runpytest()
    result.assert_outcomes(passed=9)


def test_parametrize_applies_to_describe(testdir):
    testdir.makepyfile(
        """
        import pytest

        @pytest.mark.parametrize('foo', (1, 2, 3))
        def describe_marks():

            @pytest.mark.parametrize('bar', (1, 2, 3))
            def isint(foo, bar):
                assert foo == int(foo)
                assert bar == int(bar)

            def isint2(foo):
                assert foo == int(foo)

            def describe_nested():
                def isint3(foo):
                    assert foo == int(foo)
        """)

    result = testdir.runpytest()
    result.assert_outcomes(passed=15)


def test_cartesian_parametrize_on_describe(testdir):
    testdir.makepyfile(
        """
        import pytest

        @pytest.mark.parametrize('foo', (1, 2, 3))
        @pytest.mark.parametrize('bar', (1, 2, 3))
        def describe_marks():

            def isint(foo, bar):
                assert foo == int(foo)
                assert bar == int(bar)
        """)

    result = testdir.runpytest()
    result.assert_outcomes(passed=9)


def test_parametrize_with_shared(testdir):
    testdir.makepyfile(
        """
        import pytest
        from pytest import fixture
        from pytest_describe import behaves_like

        def a_duck():
            def it_quacks(sound):
                assert sound == int(sound)


        @pytest.mark.parametrize('foo', (1, 2, 3))
        @behaves_like(a_duck)
        def describe_something_that_quacks():
            @fixture
            def sound(foo):
                return foo

        @pytest.mark.parametrize('foo', (1, 2, 3))
        @behaves_like(a_duck)
        def describe_something_that_barks():
            @fixture
            def sound(foo):
                return foo
        """)

    result = testdir.runpytest()
    result.assert_outcomes(passed=6)


def test_parametrize_with_shared_but_different_values(testdir):
    testdir.makepyfile(
        """
        import pytest
        from pytest import fixture
        from pytest_describe import behaves_like

        def a_duck():
            def it_quacks(sound):
                assert sound[1] == int(sound[1])
                assert sound[0] == 'bark' or sound[1] <= 3
                assert sound[0] == 'quack' or sound[1] >= 4


        @pytest.mark.parametrize('foo', (1, 2, 3))
        @behaves_like(a_duck)
        def describe_something_that_quacks():
            @fixture
            def sound(foo):
                return ('quack', foo)

        @pytest.mark.parametrize('foo', (4, 5, 6))
        @behaves_like(a_duck)
        def describe_something_that_barks():
            @fixture
            def sound(foo):
                return ('bark', foo)
        """)

    result = testdir.runpytest()
    result.assert_outcomes(passed=6)


def test_coincident_parametrize_at_top(testdir):
    testdir.makepyfile(
        """
        import pytest

        @pytest.mark.parametrize('foo', (1, 2, 3))
        def describe_marks():

            @pytest.mark.parametrize('bar', (1, 2, 3))
            def isint(foo, bar):
                assert foo == int(foo)
                assert bar == int(bar)

        @pytest.mark.parametrize('foo', (1, 2, 3))
        def describe_marks2():
            def isint2(foo):
                assert foo == int(foo)
        """)

    result = testdir.runpytest()
    result.assert_outcomes(passed=12)


def test_keywords(testdir):
    testdir.makepyfile(
        """
        import pytest
        def describe_a():
            def foo_test():
                pass
            def bar_test():
                pass
        """)

    result = testdir.runpytest('-k', 'foo')
    try:
        result.assert_outcomes(passed=1, deselected=1)
    except TypeError:  # pragma: no cover pytest < 7.0
        assert_outcomes(result, passed=1, deselected=1)


def test_custom_markers(testdir):
    testdir.makeini(
        """
        [pytest]
        markers =
          foo
          bar
        """)

    testdir.makepyfile(
        """
        import pytest
        def describe_a():
            @pytest.mark.foo
            def foo_test():
                pass
            @pytest.mark.bar
            def bar_test():
                pass
        """)

    result = testdir.runpytest('-m', 'foo')
    try:
        result.assert_outcomes(passed=1, deselected=1)
    except TypeError:  # pragma: no cover pytest < 7.0
        assert_outcomes(result, passed=1, deselected=1)


def test_module_marks(testdir):
    testdir.makepyfile(
        """
        import pytest
        pytestmark = [ pytest.mark.foo ]
        def describe_a():
            pytestmark = [ pytest.mark.bar ]
            def describe_b():
                def a_test():
                    pass
        """)

    result = testdir.runpytest('-m', 'foo')
    result.assert_outcomes(passed=1)


def test_mark_at_describe_function(testdir):
    testdir.makepyfile(
        """
        import pytest
        @pytest.mark.foo
        def describe_foo():
            def describe_a():
                def a_test():
                    pass
            @pytest.mark.bar
            def b_test():
                pass
        """)

    result = testdir.runpytest('-m', 'foo')
    result.assert_outcomes(passed=2)


def test_mark_stacking(testdir):
    testdir.makepyfile(
        """
        import pytest
        @pytest.fixture()
        def get_marks(request):
            return [(mark.args[0], node.name) for node, mark
                    in request.node.iter_markers_with_node(name='my_mark')]

        @pytest.mark.my_mark('foo')
        def describe_marks():
            def it_is_inherited_from_describe_block(get_marks):
                assert get_marks == [('foo', 'describe_marks')]

            @pytest.mark.my_mark('bar')
            @pytest.mark.my_mark('baz')
            def all_marks_are_chained(get_marks):
                assert get_marks == [
                    ('baz', 'all_marks_are_chained'),
                    ('bar', 'all_marks_are_chained'),
                    ('foo', 'describe_marks')]
        """)

    result = testdir.runpytest()
    result.assert_outcomes(passed=2)
