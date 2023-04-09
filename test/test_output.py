"""Test verbose output"""


def test_verbose_output(testdir):
    testdir.makepyfile(
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

    result = testdir.runpytest("-v")

    result.assert_outcomes(passed=1, failed=1)

    output = [
        ' '.join(line.split('::', 2)[2].split())
        for line in result.outlines
        if line.startswith('test_verbose_output.py::describe_something::')
    ]

    assert output == [
        "describe_nested_ok::passes PASSED [ 50%]",
        "describe_nested_bad::fails FAILED [100%]",
    ]
