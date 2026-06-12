"""Test the API for accessing describe functions of test items"""


def test_get_describe_functions(pytester):
    pytester.makepyfile(
        """
        from pytest_describe import get_describe_functions

        def describe_outer():
            '''the outer block'''

            def describe_inner():

                def it_knows_its_describe_functions(request):
                    funcs = get_describe_functions(request.node)
                    assert [func.__name__ for func in funcs] == [
                        'describe_outer', 'describe_inner']
                    assert funcs[0].__doc__ == 'the outer block'
                    assert funcs[1].__doc__ is None

        def test_outside_of_describe_blocks(request):
            assert get_describe_functions(request.node) == ()
        """
    )

    result = pytester.runpytest()

    result.assert_outcomes(passed=2)


def test_get_describe_functions_with_shared_behavior(pytester):
    pytester.makepyfile(
        """
        from pytest_describe import behaves_like, get_describe_functions

        def a_duck():

            def it_quacks(request):
                funcs = get_describe_functions(request.node)
                assert [func.__name__ for func in funcs] == [
                    'describe_something_that_quacks']

        @behaves_like(a_duck)
        def describe_something_that_quacks():
            pass
        """
    )

    result = pytester.runpytest()

    result.assert_outcomes(passed=1)
