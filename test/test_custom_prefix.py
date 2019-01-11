import py
import re

pytest_plugins = 'pytester'

ini = """
[pytest]
describe_prefixes = foo bar
"""


def test_collect_custom_prefix(testdir):
    testdir.makeini(ini)

    a_dir = testdir.mkpydir('a_dir')
    a_dir.join('test_a.py').write(py.code.Source("""
        def foo_scope():
            def bar_context():
                def passes():
                    pass
    """))

    result = testdir.runpytest('--collectonly')
    print(result.outlines)
    expected_lines = [
        re.compile("collected 1 item(s)?"),
        re.compile("\s*<Module '(a_dir/)?test_a.py'>"),
        re.compile("\s*<DescribeBlock 'foo_scope'>"),
        re.compile("\s*<DescribeBlock 'bar_context'>"),
        re.compile("\s*<Function 'passes'>"),
    ]
    for line in expected_lines:
        assert any([line.match(r) is not None for r in result.outlines])
