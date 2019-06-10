def assert_outcomes(result, **expected):
    o = result.parseoutcomes()
    del o['seconds']

    try:
        if 'warnings' in o:
            del o['warnings']
        if 'pytest-warnings' in o:
            del o['pytest-warnings']
    except KeyError:
        pass

    assert o == expected
