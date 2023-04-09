import re

from util import Source

pytest_plugins = 'pytester'

ini = """
[pytest]
describe_prefixes = foo bar
"""


def test_collect_custom_prefix(testdir):
    testdir.makeini(ini)

    a_dir = testdir.mkpydir('a_dir')
    a_dir.join('test_a.py').write(Source("""
        def foo_scope():
            def bar_context():
                def passes():
                    pass
    """))

    result = testdir.runpytest('--collectonly')
    expected_lines = map(re.compile, [
        r"collected 1 item(s)?",
        r"\s*<Module '?(a_dir/)?test_a.py'?>",
        r"\s*<DescribeBlock '?foo_scope'?>",
        r"\s*<DescribeBlock '?bar_context'?>",
        r"\s*<Function '?passes'?>",
    ])
    for line in expected_lines:
        assert any([line.match(r) is not None for r in result.outlines])
