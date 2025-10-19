"""Test verbose output"""


def test_verbose_output(pytester):
    pytester.makepyfile(
        """
        def describe_something():
            def describe_nested_ok():
                def passes():
                    assert True
            def describe_nested_bad():
                def fails():
                    assert False
        """
    )

    result = pytester.runpytest("-v")

    result.assert_outcomes(passed=1, failed=1)

    result.stdout.fnmatch_lines(
        [
            (
                "*test_verbose_output.py::describe_something::"
                "describe_nested_ok::passes PASSED*"
            ),
            (
                "*test_verbose_output.py::describe_something::"
                "describe_nested_bad::fails FAILED*"
            ),
        ]
    )
