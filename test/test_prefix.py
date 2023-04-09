"""Test custom prefixes"""


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

    output = '\n'.join(filter(None, result.outlines))
    assert """
collected 1 item
<Module test_collect_custom_prefix.py>
  <DescribeBlock 'foo_scope'>
    <DescribeBlock 'bar_context'>
      <Function passes>
""" in output
