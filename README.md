[![PyPI version](https://badge.fury.io/py/pytest-describe.svg)](https://pypi.org/project/pytest-describe/)
[![Workflow status](https://github.com/pytest-dev/pytest-describe/actions/workflows/main.yml/badge.svg)](https://github.com/pytest-dev/pytest-describe/actions)

# Describe-style plugin for pytest

**pytest-describe** is a plugin for [pytest](https://docs.pytest.org/)
that allows tests to be written in arbitrary nested describe-blocks,
similar to RSpec (Ruby) and Jasmine (JavaScript).

The main inspiration for this was
a [video](https://www.youtube.com/watch?v=JJle8L8FRy0>) by Gary Bernhardt.

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
plugins: describe-2.2.0
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
This can be used to group helper functions. Otherwise, functions inside the 
describe-blocks need not follow any special naming convention.

```python
def describe_function():

    def _helper():
        return "something"

    def it_does_something():
        value = _helper()
        ...
```


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
locally to each group of test function.

With pytest, it's possible to organize tests in a similar way with classes.
However, I think classes are awkward. I don't think the convention of using
camel-case names for classes fit very well when testing functions in different
cases. In addition, every test function must take a "self" argument that is
never used.

The pytest-describe plugin allows organizing your tests in the nicer way shown
above using describe-blocks.

## Shared Behaviors

If you've used rspec's shared examples or test class inheritance, then you may
be familiar with the benefit of having the same tests apply to
multiple "subjects" or "suts" (system under test).

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
