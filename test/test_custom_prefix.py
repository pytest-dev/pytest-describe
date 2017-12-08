import py

pytest_plugins = 'pytester'

ini = """
[pytest]
describe_prefixes = foo bar
"""


def _collect_result(result):
    lines = result.stdout.lines

    # discard last line if empty
    if lines[-1] == '':
        lines = lines[:-1]

    # workaround for older versions of pytest not pluralizing correctly
    lines = [l.replace(' 1 items', ' 1 item') for l in lines]

    return lines[-7:-2]


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
    assert _collect_result(result) == [
        "collected 1 item",
        "<Module 'a_dir/test_a.py'>",
        "  <DescribeBlock 'foo_scope'>",
        "    <DescribeBlock 'bar_context'>",
        "      <Function 'passes'>",
    ]
