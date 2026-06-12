[![PyPI version](https://badge.fury.io/py/pytest-describe.svg)](https://pypi.org/project/pytest-describe/)
[![Workflow status](https://github.com/pytest-dev/pytest-describe/actions/workflows/main.yml/badge.svg)](https://github.com/pytest-dev/pytest-describe/actions)

# Describe-style plugin for pytest

**pytest-describe** is a plugin for [pytest](https://docs.pytest.org/)
that allows tests to be written in arbitrary nested describe-blocks,
similar to RSpec (Ruby) and Jasmine (JavaScript).

The main inspiration for this was
a [video](https://www.youtube.com/watch?v=JJle8L8FRy0) by Gary Bernhardt.

## Why bother?

I've found that quite often my tests have one "dimension" more than my production
code. The production code is organized into packages, modules, classes
(sometimes), and functions. I like to organize my tests in the same way, but
tests also have different *cases* for each function. This tends to end up with
a set of tests for each module (or class), where each test has to name both a
function and a *case*. For instance:

```python
def test_my_function_with_default_arguments():
def test_my_function_with_some_other_arguments():
def test_my_function_throws_exception():
def test_my_function_handles_exception():
def test_some_other_function_returns_true():
def test_some_other_function_returns_false():
```

It's much nicer to do this:

```python
def describe_my_function():
    def with_default_arguments():
    def with_some_other_arguments():
    def it_throws_exception():
    def it_handles_exception():

def describe_some_other_function():
    def it_returns_true():
    def it_returns_false():
```

It has the additional advantage that you can have marks and fixtures that apply
locally to each group of test functions.

With pytest, it's possible to organize tests in a similar way with classes.
However, I think classes are awkward. I don't think the convention of using
camel-case names for classes fit very well when testing functions in different
cases. In addition, every test function must take a "self" argument that is
never used.

The pytest-describe plugin allows organizing your tests in the nicer way shown
above using describe-blocks.

## Installation

You guessed it:

```sh
pip install pytest-describe
```

## Usage

Pytest will automatically find the plugin and use it when you run pytest.
Running pytest will show that the plugin is loaded:

```sh
$ pytest
...
plugins: describe-3.2.0
...
```

Tests can now be written in describe-blocks.
Here is an example for testing a Wallet class:

```python
import pytest


class Wallet:

    def __init__(self, initial_amount=0):
        self.balance = initial_amount

    def spend_cash(self, amount):
        if self.balance < amount:
            raise ValueError(f'Not enough available to spend {amount}')
        self.balance -= amount

    def add_cash(self, amount):
        self.balance += amount


def describe_wallet():

    def describe_start_empty():

        @pytest.fixture
        def wallet():
            return Wallet()

        def initial_amount(wallet):
            assert wallet.balance == 0

        def add_cash(wallet):
            wallet.add_cash(80)
            assert wallet.balance == 80

        def spend_cash(wallet):
            with pytest.raises(ValueError):
                wallet.spend_cash(10)

    def describe_with_starting_balance():

        @pytest.fixture
        def wallet():
            return Wallet(20)

        def initial_amount(wallet):
            assert wallet.balance == 20

        def describe_adding():

            def add_little_cash(wallet):
                wallet.add_cash(5)
                assert wallet.balance == 25

            def add_much_cash(wallet):
                wallet.add_cash(980)
                assert wallet.balance == 1000

        def describe_spending():

            def spend_cash(wallet):
                wallet.spend_cash(15)
                assert wallet.balance == 5

            def spend_too_much_cash(wallet):
                with pytest.raises(ValueError):
                    wallet.spend_cash(25)
```

The default prefix for describe-blocks is `describe_`, but you can configure it
in the pytest/python configuration file via `describe_prefixes` or
via the command line option `--describe-prefixes`.

For example in your `pyproject.toml`:

```toml
[tool.pytest.ini_options]
describe_prefixes = ["custom_prefix_"]
```

Functions prefixed with `_` in the describe-block are not collected as tests.
This can be used to group helper functions. Thanks to closures, a helper
defined in an enclosing describe-block is visible in all nested blocks.
Otherwise, functions inside the describe-blocks need not follow any special
naming convention.

```python
def describe_function():

    def _helper():
        return "something"

    def it_does_something():
        value = _helper()
        ...
```

## Fixtures as describe arguments

When several tests in a describe-block need the same fixture, you can pass
the fixture name as an argument to the describe function instead of
repeating it in every test:

```python
import pytest


@pytest.fixture
def user():
    return create_user()


def describe_create_book(user):

    def with_valid_book(valid_book):
        ...  # use the user and valid_book fixtures

    def with_invalid_book(invalid_book):
        ...  # use the user and invalid_book fixtures
```

This is functionally equivalent to declaring the fixture as an argument of
every test in the block. In particular, parametrized fixtures generate
multiple tests as usual, and fixtures defined inside the block can use the
describe arguments as well. Shared behaviors can also declare arguments,
which are then treated like arguments of the importing describe-blocks.

Note that describe-blocks run when tests are *collected*, before any
fixture is set up. The arguments are therefore only placeholders during
collection, and the actual fixture values are injected when the tests run.
Using an argument in the describe-block body itself — anywhere outside a
test or fixture function — raises an error at collection time:

```python
def describe_create_book(user):
    name = user.name  # error: user is only available inside the tests

    def with_valid_book(valid_book):
        name = user.name  # works fine
```

For the same reason, fixtures with a scope higher than `function` and
autouse fixtures should not use describe arguments, because they may be
set up before the values are injected.

## Shared behaviors

If you've used RSpec's shared examples or test class inheritance, then you may
be familiar with the benefit of having the same tests apply to
multiple "subjects" or "SUTs" (systems under test).

```python
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
```

Fixtures defined in the block that includes the shared behavior take precedence
over fixtures defined in the shared behavior. This rule only applies to
fixtures, not to other functions (nested describe blocks and tests). Instead,
they are all collected as separate tests.

## Using docstrings as describe block names

By default, describe-blocks are reported under the name of their function,
e.g. `describe_wallet`. If you want more descriptive test reports, you can
set the `describe_docstrings` configuration option, e.g. in your
`pyproject.toml`:

```toml
[tool.pytest.ini_options]
describe_docstrings = true
```

Describe-blocks are then named after the first line of the docstring of
their describe function, if it has one:

```python
def describe_wallet():
    """a wallet"""

    def describe_when_empty():
        """when it is empty"""

        def it_has_no_balance(wallet):
            assert wallet.balance == 0
```

This will be reported as:

```text
test_wallet.py::a wallet::when it is empty::it_has_no_balance PASSED
```

Note that the docstring-based names become part of the test node IDs, which
are used when selecting tests with `-k` or by node ID on the command line.

## Accessing describe functions from plugins

Reporting plugins sometimes need to know which describe-blocks enclose a
given test, e.g. to show their docstrings in the test report. For this
purpose, pytest-describe provides the function `get_describe_functions`
that returns the describe functions wrapping a collected test item,
starting with the outermost block:

```python
from pytest_describe import get_describe_functions

def pytest_collection_modifyitems(items):
    for item in items:
        for func in get_describe_functions(item):
            print(item.nodeid, func.__name__, func.__doc__)
```
