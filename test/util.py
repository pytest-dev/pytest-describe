def assert_outcomes(result, **expected):
    o = result.parseoutcomes()
    del o['seconds']
    assert o == expected
