from util import Source

pytest_plugins = 'pytester'


def test_verbose_output(testdir):
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

    result = testdir.runpytest('-v')
    expected = [
        'a_dir/test_a.py::describe_something::describe_nested_bad::'
        'fails FAILED',
        'a_dir/test_a.py::describe_something::describe_nested_ok::'
        'passes PASSED',
    ]
    for line in expected:
        assert any(out for out in result.outlines if out.startswith(line))
