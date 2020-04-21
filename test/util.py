def assert_outcomes(result, **expected):
    outcomes = result.parseoutcomes()

    for key in 'seconds', 'warnings':
        if key in outcomes:
            del outcomes[key]

    assert outcomes == expected
