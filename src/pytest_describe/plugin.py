"""The pytest-describe plugin"""

from __future__ import annotations

import inspect
import sys
import types
from collections.abc import Callable, Iterable, Iterator
from typing import Any, NoReturn

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


class DescribeArgumentError(Exception):
    """Error raised when a describe argument is used outside of tests."""


class DescribeArgument:
    """Placeholder for a fixture passed as argument to a describe block.

    Describe blocks run at collection time, when fixtures are not yet
    available. The real fixture value is injected into the closure cells
    before each test runs. Using the placeholder itself raises an error.
    """

    __slots__ = ("name",)

    def __init__(self, name: str) -> None:
        self.name = name

    def __repr__(self) -> str:
        return (
            f"<describe argument {self.name!r}"
            " (the fixture is only available inside tests)>"
        )

    def _used(self, *args: Any, **kwargs: Any) -> NoReturn:
        raise DescribeArgumentError(
            f"The argument {self.name!r} is a placeholder for a fixture"
            " that is only available inside the tests of the describe"
            " block, it cannot be used in the describe block itself."
        )

    __call__ = __getattr__ = __getitem__ = __setitem__ = __delitem__ = _used
    __iter__ = __contains__ = __len__ = __bool__ = _used
    __eq__ = __ne__ = __lt__ = __le__ = __gt__ = __ge__ = _used
    __add__ = __sub__ = __mul__ = __truediv__ = _used
    __hash__ = object.__hash__


def get_describe_args(func: Callable[..., Any]) -> tuple[str, ...]:
    """Get the fixture names a describe block declares as parameters.

    Mirroring how pytest determines fixture names for test functions,
    only mandatory (non-defaulted) named parameters are considered.
    """
    return tuple(
        name
        for name, param in inspect.signature(func).parameters.items()
        if param.kind in (param.POSITIONAL_OR_KEYWORD, param.KEYWORD_ONLY)
        and param.default is param.empty
    )


def find_argument_cells(namespace: dict[str, Any]) -> dict[str, list[types.CellType]]:
    """Find closure cells holding describe arguments in collected functions.

    Cells are shared between all nested functions referencing the same
    outer variable, but the same argument name can appear in multiple
    cells, e.g. when a describe block and an imported shared behavior
    both declare an argument with the same name.
    """
    cells: dict[str, list[types.CellType]] = {}
    for obj in namespace.values():
        # Unwrap fixture function definitions (pytest >= 8.4)
        func = inspect.unwrap(obj) if is_fixture_function_definition(obj) else obj
        if not isinstance(func, types.FunctionType):
            continue
        for cell in func.__closure__ or ():
            try:
                contents = cell.cell_contents
            except ValueError:  # pragma: no cover (empty cell)
                continue
            if isinstance(contents, DescribeArgument):
                name_cells = cells.setdefault(contents.name, [])
                # check identity, equality would compare cell contents
                if not any(c is cell for c in name_cells):
                    name_cells.append(cell)
    return cells


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


def make_module_from_function(
    func: types.FunctionType, args: tuple[str, ...] = ()
) -> types.ModuleType:
    """Evaluate the local scope of a function as if it was a module."""
    module = types.ModuleType(func.__name__)

    # Import shared behaviors into the generated module. We do this before
    # importing the direct children, so that fixtures in the block that's
    # importing the behavior take precedence.
    for shared_func in getattr(func, "_behaves_like", ()):
        module.__dict__.update(evaluate_shared_behavior(shared_func))

    # Import children, passing placeholders for declared fixture arguments.
    # Placeholders are removed from the namespace; note that this includes
    # arguments of outer describe blocks appearing here as free variables.
    funclocals = {
        name: obj
        for name, obj in trace_function(
            func, **{name: DescribeArgument(name) for name in args}
        ).items()
        if not isinstance(obj, DescribeArgument)
    }
    module.__dict__.update(funclocals)
    return module


def evaluate_shared_behavior(func: types.FunctionType) -> dict[str, Any]:
    """Evaluate the local scope of a function."""
    try:
        shared_functions: dict[str, Any] = func._shared_functions  # type: ignore[attr-defined]
    except AttributeError:
        shared_functions = {}
        funclocals = trace_function(
            func,
            **{name: DescribeArgument(name) for name in get_describe_args(func)},
        )
        for name, obj in funclocals.items():
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

    describe_args: tuple[str, ...]
    describe_cells: dict[str, list[types.CellType]]

    @classmethod
    def from_parent(  # type: ignore[override]
        cls, parent: pytest.Collector, obj: types.FunctionType
    ) -> DescribeBlock:
        """Construct a new node for the describe block"""
        name = getattr(obj, "_mangled_name", obj.__name__)
        if parent.config.getini("describe_docstrings"):
            doc = inspect.getdoc(obj)
            if doc:
                name = doc.splitlines()[0].strip()
        nodeid = parent.nodeid + "::" + name
        self: DescribeBlock = super().from_parent(
            parent=parent, path=parent.path, nodeid=nodeid
        )
        self.name = name
        self.funcobj = obj  # type: ignore[assignment]
        self.describe_args = get_describe_args(obj)
        self.describe_cells = {}
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
        module = make_module_from_function(
            self.funcobj,  # type: ignore[arg-type]
            self.describe_args,
        )
        # Arguments of imported shared behaviors are treated like
        # arguments of the describe block that imports the behavior.
        for shared_func in getattr(self.funcobj, "_behaves_like", ()):
            for name in get_describe_args(shared_func):
                if name not in self.describe_args:
                    self.describe_args += (name,)
        self.describe_cells = find_argument_cells(module.__dict__)
        if self.describe_args:
            # Provide the autouse fixture that injects the fixture values
            # into the closure cells before each test in this block.
            module.__dict__[INJECTOR_FIXTURE_NAME] = make_injector_fixture()
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


def get_describe_functions(
    node: pytest.Item | pytest.Collector,
) -> tuple[types.FunctionType, ...]:
    """Get the functions of the describe blocks enclosing the given node.

    The functions are returned in the order of nesting, starting with the
    outermost describe block. Reporting plugins can use this function to
    access the original describe functions and e.g. their docstrings.
    """
    return tuple(
        block.funcobj  # type: ignore[misc]
        for block in node.listchain()
        if isinstance(block, DescribeBlock)
    )


def pytest_pycollect_makeitem(
    collector: pytest.Collector, name: str, obj: object
) -> DescribeBlock | None:
    """Collect items from describe blocks."""
    if isinstance(obj, types.FunctionType):
        for prefix in collector.config.getini("describe_prefixes"):
            if obj.__name__.startswith(prefix):
                return DescribeBlock.from_parent(collector, obj)
    return None


# Since pytest 8.1, FixtureManager.getfixturedefs takes the node itself
# instead of its node id.
_getfixturedefs_takes_node = pytest.version_tuple >= (8, 1)


@pytest.hookimpl(tryfirst=True)
def pytest_generate_tests(metafunc: pytest.Metafunc) -> None:
    """Add fixtures declared as describe arguments to the fixture closure.

    This makes pytest resolve these fixtures for every test in the block,
    including generating parametrized tests for parametrized fixtures.
    """
    definition = metafunc.definition
    arg_names = [
        name
        for node in definition.listchain()
        if isinstance(node, DescribeBlock)
        for name in node.describe_args
    ]
    if not arg_names:
        return
    fixturemanager = definition.session._fixturemanager
    fixtureinfo = definition._fixtureinfo
    node = definition if _getfixturedefs_takes_node else definition.nodeid
    seen = set(metafunc.fixturenames)
    for arg_name in arg_names:
        if arg_name in seen:
            continue
        seen.add(arg_name)
        # metafunc.fixturenames is the same list as the names_closure
        # of the fixture info used by the test item later
        metafunc.fixturenames.append(arg_name)
        # the name must also be in initialnames, otherwise it is removed
        # again by prune_dependency_tree() when the test is parametrized
        # (since pytest 9, FuncFixtureInfo is a frozen dataclass)
        object.__setattr__(
            fixtureinfo, "initialnames", (*fixtureinfo.initialnames, arg_name)
        )
        # register the fixture definitions of the added fixture and its
        # transitive dependencies, so that parametrized fixtures multiply
        # the tests even when they are only used indirectly
        pending = [arg_name]
        while pending:
            dep_name = pending.pop()
            fixturedefs = fixturemanager.getfixturedefs(
                dep_name,
                node,  # type: ignore[arg-type]  # node id before pytest 8.1
            )
            if not fixturedefs:
                continue  # not a fixture (e.g. 'request'), fails at setup
            metafunc._arg2fixturedefs[dep_name] = list(fixturedefs)
            for dep in fixturedefs[-1].argnames:
                if dep not in seen:
                    seen.add(dep)
                    metafunc.fixturenames.append(dep)
                    pending.append(dep)


def gather_describe_cells(item: pytest.Item) -> dict[str, list[types.CellType]]:
    """Collect the argument cells of all describe blocks enclosing a test."""
    cells: dict[str, list[types.CellType]] = {}
    for node in item.listchain():
        if isinstance(node, DescribeBlock):
            for name, name_cells in node.describe_cells.items():
                all_cells = cells.setdefault(name, [])
                for cell in name_cells:
                    # check identity, equality would compare cell contents
                    if not any(c is cell for c in all_cells):
                        all_cells.append(cell)
    return cells


INJECTOR_FIXTURE_NAME = "_pytest_describe_inject"


def inject_describe_fixtures(request: pytest.FixtureRequest) -> Iterator[None]:
    """Inject fixture values into the closure cells of describe arguments.

    Used as an autouse fixture in describe blocks with arguments, so that
    the values are already injected when other fixtures of the block run.
    The placeholders are restored when the fixture is torn down.
    """
    saved: list[tuple[types.CellType, Any]] = []
    for name, name_cells in gather_describe_cells(request.node).items():
        value = request.getfixturevalue(name)
        for cell in name_cells:
            saved.append((cell, cell.cell_contents))
            cell.cell_contents = value
    yield
    for cell, old_value in reversed(saved):
        cell.cell_contents = old_value


def make_injector_fixture() -> Any:
    """Create the autouse fixture that injects describe arguments.

    The fixture must be created lazily here, because fixtures defined in
    the plugin module itself would be registered as global fixtures.
    """
    return pytest.fixture(autouse=True, name=INJECTOR_FIXTURE_NAME)(
        inject_describe_fixtures
    )


def pytest_addoption(parser: pytest.Parser) -> None:
    """Add configuration option describe_prefixes."""
    parser.addini(
        "describe_prefixes",
        type="args",
        default=("describe",),
        help="prefixes for Python describe function discovery",
    )
    parser.addini(
        "describe_docstrings",
        type="bool",
        default=False,
        help="use docstrings as names for describe blocks",
    )
