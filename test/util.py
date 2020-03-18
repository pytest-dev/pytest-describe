def assert_outcomes(result, **expected):
    outcomes = result.parseoutcomes()

    for key in 'seconds', 'pytest-warnings', 'warnings', 'warning':
        if key in outcomes:
            del outcomes[key]

    assert outcomes == expected
