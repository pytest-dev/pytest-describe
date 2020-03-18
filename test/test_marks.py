import py
from util import assert_outcomes

pytest_plugins = 'pytester'


def test_special_marks(testdir):
    a_dir = testdir.mkpydir('a_dir')
    a_dir.join('test_a.py').write(py.code.Source("""
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
    """))

    result = testdir.runpytest()
    assert_outcomes(result, passed=3, xfailed=1, xpassed=1, skipped=1)


def test_keywords(testdir):
    a_dir = testdir.mkpydir('a_dir')
    a_dir.join('test_a.py').write(py.code.Source("""
        import pytest
        def describe_a():
            @pytest.mark.foo
            def foo_test():
                pass
            @pytest.mark.bar
            def bar_test():
                pass
    """))

    result = testdir.runpytest('-k', 'foo')
    assert_outcomes(result, passed=1, deselected=1)


def test_marks(testdir):
    a_dir = testdir.mkpydir('a_dir')
    a_dir.join('test_a.py').write(py.code.Source("""
        import pytest
        def describe_a():
            @pytest.mark.foo
            def foo_test():
                pass
            @pytest.mark.bar
            def bar_test():
                pass
    """))

    result = testdir.runpytest('-m', 'foo')
    assert_outcomes(result, passed=1, deselected=1)


def test_module_marks(testdir):
    a_dir = testdir.mkpydir('a_dir')
    a_dir.join('test_a.py').write(py.code.Source("""
        import pytest
        pytestmark = [ pytest.mark.foo ]
        def describe_a():
            pytestmark = [ pytest.mark.bar ]
            def describe_b():
                def a_test():
                    pass
    """))

    result = testdir.runpytest('-m', 'foo')
    assert_outcomes(result, passed=1)


def test_mark_at_describe_function(testdir):
    a_dir = testdir.mkpydir('a_dir')
    a_dir.join('test_a.py').write(py.code.Source("""
        import pytest
        @pytest.mark.foo
        def describe_foo():
            def describe_a():
                def a_test():
                    pass
            @pytest.mark.bar
            def b_test():
                pass
    """))

    result = testdir.runpytest('-m', 'foo')
    assert_outcomes(result, passed=2)
