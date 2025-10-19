"""Test custom prefixes"""


def test_collect_custom_prefix(pytester):
    pytester.makeini(
        """
        [pytest]
        describe_prefixes = foo bar
        """
    )

    pytester.makepyfile(
        """
        def foo_scope():
            def bar_context():
                def passes():
                    pass
        """
    )

    result = pytester.runpytest("--collectonly")
    result.assert_outcomes()

    result.stdout.fnmatch_lines(
        [
            "*collected 1 item*",
            "*<Module test_collect_custom_prefix.py>",
            "*<DescribeBlock 'foo_scope'>",
            "*<DescribeBlock 'bar_context'>",
            "*<Function passes>",
        ]
    )
