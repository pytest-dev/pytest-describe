"""Test custom prefixes"""

from textwrap import dedent


def test_collect_custom_prefix(testdir):
    testdir.makeini(
        """
        [pytest]
        describe_prefixes = foo bar
        """)

    testdir.makepyfile(
        """
        def foo_scope():
            def bar_context():
                def passes():
                    pass
        """)

    result = testdir.runpytest('--collectonly')
    result.assert_outcomes()

    output = '\n'.join(line.lstrip() for line in result.outlines if line)
    assert "collected 1 item" in output
    assert dedent("""
        <Module test_collect_custom_prefix.py>
        <DescribeBlock 'foo_scope'>
        <DescribeBlock 'bar_context'>
        <Function passes>
        """) in output
