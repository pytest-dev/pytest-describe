from util import assert_outcomes, Source

pytest_plugins = 'pytester'


def test_can_pass(testdir):
    a_dir = testdir.mkpydir('a_dir')
    a_dir.join('test_a.py').write(Source("""
        def describe_something():
            def passes():
                assert True
            def describe_nested():
                def passes_too():
                    assert True
    """))

    result = testdir.runpytest()
    assert_outcomes(result, passed=2)


def test_can_fail(testdir):
    a_dir = testdir.mkpydir('a_dir')
    a_dir.join('test_a.py').write(Source("""
        def describe_something():
            def fails():
                assert False
            def describe_nested():
                def fails_too():
                    assert False
    """))

    result = testdir.runpytest()
    assert_outcomes(result, failed=2)


def test_can_fail_and_pass(testdir):
    a_dir = testdir.mkpydir('a_dir')
    a_dir.join('test_a.py').write(Source("""
        def describe_something():
            def describe_nested_ok():
                def passes():
                    assert True
            def describe_nested_bad():
                def fails():
                    assert False
    """))

    result = testdir.runpytest()
    assert_outcomes(result, passed=1, failed=1)
