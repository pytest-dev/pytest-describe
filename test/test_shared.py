import py
from util import assert_outcomes

pytest_plugins = 'pytester'


def test_shared_behavior(testdir):
    a_dir = testdir.mkpydir('a_dir')
    a_dir.join('test_something.py').write(py.code.Source("""
        from pytest import fixture
        from pytest_describe import behaves_like

        def a_duck():
            def it_quacks(sound):
                assert sound == "quack"

        @behaves_like(a_duck)
        def describe_something_that_quacks():
            @fixture
            def sound():
                return "quack"

        @behaves_like(a_duck)
        def describe_something_that_barks():
            @fixture
            def sound():
                return "bark"
    """))

    result = testdir.runpytest()
    assert_outcomes(result, failed=1, passed=1)


def test_multiple_shared_behaviors(testdir):
    a_dir = testdir.mkpydir('a_dir')
    a_dir.join('test_something.py').write(py.code.Source("""
        from pytest import fixture
        from pytest_describe import behaves_like

        def a_duck():
            def it_quacks(sound):
                assert sound == "quack"

        def a_bird():
            def it_flies(medium):
                assert medium == "air"

        def describe_birds():
            @fixture
            def medium():
                return "air"

            @behaves_like(a_duck, a_bird)
            def describe_something_that_quacks():
                @fixture
                def sound():
                    return "quack"

            @behaves_like(a_duck, a_bird)
            def describe_something_that_barks():
                @fixture
                def sound():
                    return "bark"
    """))

    result = testdir.runpytest()
    assert_outcomes(result, failed=1, passed=3)


def test_fixture(testdir):
    a_dir = testdir.mkpydir('a_dir')
    a_dir.join('test_something.py').write(py.code.Source("""
        from pytest import fixture
        from pytest_describe import behaves_like

        def a_duck():
            @fixture
            def sound():
                return "quack"

            def it_quacks(sound):
                assert sound == "quack"

        @behaves_like(a_duck)
        def describe_a_normal_duck():
            pass
    """))

    result = testdir.runpytest('-v')
    assert_outcomes(result, passed=1)


def test_override_fixture(testdir):
    a_dir = testdir.mkpydir('a_dir')
    a_dir.join('test_something.py').write(py.code.Source("""
        from pytest import fixture
        from pytest_describe import behaves_like

        def a_duck():
            @fixture
            def sound():
                return "quack"

            def it_quacks(sound):
                assert sound == "quack"

        @behaves_like(a_duck)
        def describe_something_that_barks():
            @fixture
            def sound():
                return "bark"
    """))

    result = testdir.runpytest('-v')
    assert_outcomes(result, failed=1)


def test_name_mangling(testdir):
    a_dir = testdir.mkpydir('a_dir')
    a_dir.join('test_something.py').write(py.code.Source("""
        from pytest import fixture
        from pytest_describe import behaves_like

        def thing():
            foo = 42
            def it_does_something():
                assert foo == 42

        @behaves_like(thing)
        def describe_something():
            foo = 4242
            def it_does_something():
                assert foo == 4242
    """))

    result = testdir.runpytest('-v')
    assert_outcomes(result, passed=2)


def test_nested_name_mangling(testdir):
    a_dir = testdir.mkpydir('a_dir')
    a_dir.join('test_something.py').write(py.code.Source("""
        from pytest import fixture
        from pytest_describe import behaves_like

        def thing():
            def it_does_something():
                pass
            def describe_thing():
                def it_does_something():
                    pass
                def describe_thing():
                    def it_does_something():
                        pass

        @behaves_like(thing)
        def describe_thing():
            def it_does_something():
                pass
            def describe_thing():
                def it_does_something():
                    pass
    """))

    result = testdir.runpytest('-v')
    assert_outcomes(result, passed=5)


def test_evaluated_once(testdir):
    a_dir = testdir.mkpydir('a_dir')
    a_dir.join('test_something.py').write(py.code.Source("""
        from pytest import fixture
        from pytest_describe import behaves_like

        count = 0
        def thing():
            global count
            count += 1
            def is_evaluated_once():
                assert count == 1

        @behaves_like(thing)
        def describe_something():
            pass
        @behaves_like(thing)
        def describe_something_else():
            pass
    """))

    result = testdir.runpytest('-v')
    assert_outcomes(result, passed=2)
