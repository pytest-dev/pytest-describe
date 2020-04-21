.. image:: https://badge.fury.io/py/pytest-describe.svg
    :target: https://pypi.org/project/pytest-describe/
    :alt: PyPI version

.. image:: https://travis-ci.org/pytest-dev/pytest-describe.svg?branch=master
    :target: https://travis-ci.org/pytest-dev/pytest-describe
    :alt: Travis CI

Describe-style plugin for pytest
================================

pytest-describe is a plugin for pytest that allows tests to be written in
arbitrary nested describe-blocks, similar to RSpec (Ruby) and Jasmine
(JavaScript).

The main inspiration for this was a `video
<https://www.youtube.com/watch?v=JJle8L8FRy0>`_ by Gary Bernhardt.

Installation
------------

You guessed it::

    pip install pytest-describe


Example
-------

.. code-block:: python

    def describe_list():

        @pytest.fixture
        def list():
            return []

        def describe_append():

            def adds_to_end_of_list(list):
                list.append('foo')
                list.append('bar')
                assert list == ['foo', 'bar']

        def describe_remove():

            @pytest.fixture
            def list():
                return ['foo', 'bar']

            def removes_item_from_list(list):
                list.remove('foo')
                assert list == ['bar']


Why bother?
===========

I've found that quite often my tests have one "dimension" more than my production
code. The production code is organized into packages, modules, classes
(sometimes), and functions. I like to organize my tests in the same way, but
tests also have different *cases* for each function. This tends to end up with
a set of tests for each module (or class), where each test has to name both a
function and a *case*. For instance:

.. code-block:: python

    def test_my_function_with_default_arguments():
    def test_my_function_with_some_other_arguments():
    def test_my_function_throws_exception():
    def test_my_function_handles_exception():
    def test_some_other_function_returns_true():
    def test_some_other_function_returns_false():

It's much nicer to do this:

.. code-block:: python

    def describe_my_function():
        def with_default_arguments():
        def with_some_other_arguments():
        def it_throws_exception():
        def it_handles_exception():

    def describe_some_other_function():
        def it_returns_true():
        def it_returns_false():

It has the additional advantage that you can have marks and fixtures that apply
locally to each group of test function.

With pytest, it's possible to organize tests in a similar way with classes.
However, I think classes are awkward. I don't think the convention of using
camel-case names for classes fit very well when testing functions in different
cases. In addition, every test function must take a "self" argument that is
never used.

The pytest-describe plugin allows organizing your tests in the nicer way shown
above using describe-blocks. The functions inside the describe-blocks need not
follow any special naming convention, they are always executed as tests unless
they start with an underscore. The functions used for describe-blocks must
start with ``describe_``, but you can configure this prefix with the setting
``describe_prefixes`` in the pytest configuration file.


Shared Behaviors
================

If you've used rspec's shared examples or test class inheritance, then you may
be familiar with the benefit of having the same tests apply to
multiple "subjects" or "suts" (system under test).

.. code-block:: python

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

        # the it_quacks test in this describe will pass

    @behaves_like(a_duck)
    def describe_something_that_barks():
        @fixture
        def sound():
            return "bark"

        # the it_quacks test in this describe will fail (as expected)

Fixtures defined in the block that includes the shared behavior take precedence
over fixtures defined in the shared behavior. This rule only applies to
fixtures, not to other functions (nested describe blocks and tests). Instead,
they are all collected as separate tests.
