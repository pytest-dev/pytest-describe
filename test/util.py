def assert_outcomes(result, **expected):
    o = result.parseoutcomes()
    del o['seconds']

    try:
        del o['pytest-warnings']
    except KeyError:
        pass

    assert o == expected
