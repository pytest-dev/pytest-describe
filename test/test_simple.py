"""Test simple execution"""


def test_can_pass(testdir):
    testdir.makepyfile(
        """
        def describe_something():
            def passes():
                assert True
            def describe_nested():
                def passes_too():
                    assert True
        """)

    result = testdir.runpytest()
    result.assert_outcomes(passed=2)


def test_can_fail(testdir):
    testdir.makepyfile(
        """
        def describe_something():
            def fails():
                assert False
            def describe_nested():
                def fails_too():
                    assert False
        """)

    result = testdir.runpytest()
    result.assert_outcomes(failed=2)


def test_can_fail_and_pass(testdir):
    testdir.makepyfile(
        """
        def describe_something():
            def describe_nested_ok():
                def passes():
                    assert True
            def describe_nested_bad():
                def fails():
                    assert False
        """)

    result = testdir.runpytest()
    result.assert_outcomes(passed=1, failed=1)


def test_can_run_async_tests(testdir):
    testdir.makepyfile(
        """
        import asyncio
        import pytest

        @pytest.mark.asyncio
        async def describe_something():
            async def describe_nested_ok():
                async def passes():
                    assert True
            async def describe_nested_bad():
                async def fails():
                    assert False
        """)
    result = testdir.runpytest()
    result.assert_outcomes(passed=1, failed=1)
