import py
from util import assert_outcomes

pytest_plugins = 'pytester'


def test_marks(testdir):
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
