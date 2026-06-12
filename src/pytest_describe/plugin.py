"""The pytest-describe plugin"""

from __future__ import annotations

import sys
import types
from collections.abc import Callable, Iterable
from typing import Any

import pytest

try:
    from _pytest.fixtures import FixtureFunctionDefinition
except ImportError:  # pragma: no cover (pytest < 8.4)

    def is_function_or_fixture(obj: object) -> bool:
        return isinstance(obj, types.FunctionType)

    def is_fixture_function_definition(obj: object) -> bool:
        return hasattr(obj, "_pytestfixturefunction")
else:

    def is_function_or_fixture(obj: object) -> bool:
        return isinstance(obj, types.FunctionType | FixtureFunctionDefinition)

    def is_fixture_function_definition(obj: object) -> bool:
        return isinstance(obj, FixtureFunctionDefinition)


def trace_function(
    func: Callable[..., Any], *args: Any, **kwargs: Any
) -> dict[str, Any]:
    """Call a function and return its locals."""
    f_locals: dict[str, Any] = {}

    def _trace_func(
        frame: types.FrameType, event: str, arg: Any
    ) -> None:  # pragma: no cover
        # Activate local trace for first call only
        back = frame.f_back
        if (
            back is not None
            and back.f_locals.get("_trace_func") is _trace_func
            and event == "return"
        ):
            f_locals.update(frame.f_locals)

    sys.setprofile(_trace_func)
    try:
        func(*args, **kwargs)
    finally:
        sys.setprofile(None)

    return f_locals


def make_module_from_function(func: types.FunctionType) -> types.ModuleType:
    """Evaluate the local scope of a function as if it was a module."""
    module = types.ModuleType(func.__name__)

    # Import shared behaviors into the generated module. We do this before
    # importing the direct children, so that fixtures in the block that's
    # importing the behavior take precedence.
    for shared_func in getattr(func, "_behaves_like", ()):
        module.__dict__.update(evaluate_shared_behavior(shared_func))

    # Import children
    module.__dict__.update(trace_function(func))
    return module


def evaluate_shared_behavior(func: types.FunctionType) -> dict[str, Any]:
    """Evaluate the local scope of a function."""
    try:
        shared_functions: dict[str, Any] = func._shared_functions  # type: ignore[attr-defined]
    except AttributeError:
        shared_functions = {}
        for name, obj in trace_function(func).items():
            # Only functions and fixtures are relevant here
            if not is_function_or_fixture(obj):
                continue
            # Mangle names of imported functions, except fixtures
            # because we want fixtures to be overridden in the block
            # that's importing the behavior.
            if not is_fixture_function_definition(obj):
                name = obj._mangled_name = f"{func.__name__}::{name}"
            shared_functions[name] = obj
        func._shared_functions = shared_functions  # type: ignore[attr-defined]
    return shared_functions


class DescribeBlock(pytest.Module):
    """Module-like object representing the scope of a describe block"""

    # Note: mypy applies the descriptor protocol to class-level attributes
    # of type FunctionType, so we need to ignore some errors when using it.
    funcobj: types.FunctionType

    @classmethod
    def from_parent(  # type: ignore[override]
        cls, parent: pytest.Collector, obj: types.FunctionType
    ) -> DescribeBlock:
        """Construct a new node for the describe block"""
        name = getattr(obj, "_mangled_name", obj.__name__)
        nodeid = parent.nodeid + "::" + name
        self: DescribeBlock = super().from_parent(
            parent=parent, path=parent.path, nodeid=nodeid
        )
        self.name = name
        self.funcobj = obj  # type: ignore[assignment]
        return self

    def collect(self) -> Iterable[pytest.Item | pytest.Collector]:
        """Get list of children"""
        self.session._fixturemanager.parsefactories(self)
        return super().collect()

    def _getobj(self) -> types.ModuleType:
        """Get the underlying Python object"""
        return self._importtestmodule()

    def _importtestmodule(self) -> types.ModuleType:
        """Import a describe block as if it was a module"""
        module = make_module_from_function(self.funcobj)  # type: ignore[arg-type]
        self.own_markers = getattr(self.funcobj, "pytestmark", [])
        return module

    def funcnamefilter(self, name: str) -> bool:
        """Treat all nested functions as tests

        We do not require the 'test_' prefix for the specs.
        """
        return not name.startswith("_")

    def classnamefilter(self, name: str) -> bool:
        """Don't allow test classes inside describe"""
        return False

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} {self.name!r}>"


def pytest_pycollect_makeitem(
    collector: pytest.Collector, name: str, obj: object
) -> DescribeBlock | None:
    """Collect items from describe blocks."""
    if isinstance(obj, types.FunctionType):
        for prefix in collector.config.getini("describe_prefixes"):
            if obj.__name__.startswith(prefix):
                return DescribeBlock.from_parent(collector, obj)
    return None


def pytest_addoption(parser: pytest.Parser) -> None:
    """Add configuration option describe_prefixes."""
    parser.addini(
        "describe_prefixes",
        type="args",
        default=("describe",),
        help="prefixes for Python describe function discovery",
    )
