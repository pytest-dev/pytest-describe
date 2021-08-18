import contextlib
import dis
import functools
import inspect
import sys
import types
from collections import namedtuple
from _pytest.python import PyCollector

import pprint

# Dummy objects that are passed as arguments to the describe blocks and are
# later used to determine which fixture to inject into the test function's
# closure.
InjectFixture = namedtuple('_InjectFixture', ['name'])


def accesses_arguments(funcobj):
    """Inspect a function's bytecode to determine if it uses its parameters.

    Used to determine whether the describe block itself may attempt to use the
    dummy arguments we pass to it. Note that this may produce false positives.
    """
    # LOAD_DEREF is used to access free variables from a closure, so parameters
    # from an outer function. LOAD_FAST is used to load parameters of the
    # function itself.
    parent_params = {
        arg.name for arg in getattr(funcobj, '_parent_fixture_args', set())}
    params = set(inspect.signature(funcobj).parameters) | parent_params

    return any(
        instr.opname in ('LOAD_DEREF', 'LOAD_FAST') and instr.argval in params
        for instr in dis.get_instructions(funcobj))


def raise_if_cannot_change_closure():
    """Raise if we cannot change the closure in this Python version."""
    def outer(x):
        def inner():
            return x
        return inner
    inner = outer(1)
    try:
        inner.__closure__[0].cel_contents = 2
    except err:  # Not sure which exception it could be
        raise PyCollector.CollectError(
            'Passing fixture names to describe blocks is not supported in this'
            'Python version') from err

    if inner() != 2:
        raise PyCollector.CollectError(
            'Passing fixture names to describe blocks is not supported in this'
            'Python version')


def construct_injected_fixture_args(funcobj):
    """Construct a set of dummy arguments that mark fixture injections."""
    # TODO: How do we handle kw-only args, args with defaults?
    return set(map(InjectFixture, inspect.signature(funcobj).parameters))


def inject_fixtures(func, fixture_args):
    if not isinstance(func, types.FunctionType):
        return func

    if hasattr(func, '_pytestfixturefunction'):
        # TODO: How should we handle fixtures?
        return func

    if func.__name__.startswith('describe_'):
        # FIXME: Allow customisation of describe prefix
        return func

    # Store all fixture args in all local functions. This is necessary for
    # nested describe blocks.
    func._parent_fixture_args = fixture_args

    @contextlib.contextmanager
    def _temp_change_cell(cell, new_value):
        old_value = cell.cell_contents
        cell.cell_contents = new_value
        yield
        cell.cell_contents = old_value

    # Wrap the function in an extended function that takes the fixtures
    # and updates the closure
    def wrapped(request, **kwargs):
        # Use the request fixture to get fixture values, and either feed those
        # as parameters or inject them into the closure
        with contextlib.ExitStack() as exit_stack:
            for cell in (func.__closure__ or []):
                if not isinstance(cell.cell_contents, InjectFixture):
                    continue
                fixt_value = request.getfixturevalue(cell.cell_contents.name)
                exit_stack.enter_context(_temp_change_cell(cell, fixt_value))

            direct_params = {}
            for param in inspect.signature(func).parameters:
                if param in kwargs:
                    direct_params[param] = kwargs[param]
                else:
                    direct_params[param] = request.getfixturevalue(param)

            func(**direct_params)

    if hasattr(func, 'pytestmark'):
        wrapped.pytestmark = func.pytestmark

    return wrapped


def trace_function(funcobj, *args, **kwargs):
    """Call a function, and return its locals, wrapped to inject fixtures"""
    if accesses_arguments(funcobj):
        # Since describe blocks run during test collection rather than
        # execution, fixture results aren't available. Although dereferencing
        # our dummy objects will not directly lead to an error, it would surely
        # lead to unexpected results.
        raise PyCollector.CollectError(
            'Describe blocks must not directly dereference their fixture '
            'arguments')

    funclocals = {}

    def _tracefunc(frame, event, arg):
        # Activate local trace for first call only
        if frame.f_back.f_locals.get('_tracefunc') == _tracefunc:
            if event == 'return':
                funclocals.update(frame.f_locals)

    direct_fixture_args = construct_injected_fixture_args(funcobj)
    parent_fixture_args = getattr(funcobj, '_parent_fixture_args', set())

    sys.setprofile(_tracefunc)
    try:
        # TODO: Are *args and **kwargs necessary here?
        funcobj(*direct_fixture_args, *args, **kwargs)
    finally:
        sys.setprofile(None)

    return {
        name: inject_fixtures(obj, direct_fixture_args | parent_fixture_args)
        for name, obj in funclocals.items()}


def make_module_from_function(funcobj):
    """Evaluates the local scope of a function, as if it was a module"""
    module = types.ModuleType(funcobj.__name__)

    # Import shared behaviors into the generated module. We do this before
    # importing the direct children, so that fixtures in the block that's
    # importing the behavior take precedence.
    for shared_funcobj in getattr(funcobj, '_behaves_like', []):
        module.__dict__.update(evaluate_shared_behavior(shared_funcobj))

    # Import children
    module.__dict__.update(trace_function(funcobj))
    return module


def evaluate_shared_behavior(funcobj):
    if not hasattr(funcobj, '_shared_functions'):
        funcobj._shared_functions = {}
        # TODO: What to do with fixtures in shared behavior closures?
        for name, obj in trace_function(funcobj).items():
            # Only functions are relevant here
            if not isinstance(obj, types.FunctionType):
                continue

            # Mangle names of imported functions, except fixtures because we
            # want fixtures to be overridden in the block that's importing the
            # behavior.
            if not hasattr(obj, '_pytestfixturefunction'):
                name = obj._mangled_name = f"{funcobj.__name__}::{name}"

            funcobj._shared_functions[name] = obj
    return funcobj._shared_functions


class DescribeBlock(PyCollector):
    """Module-like object representing the scope of a describe block"""

    @classmethod
    def from_parent(cls, parent, obj):
        name = obj.__name__
        try:
            from_parent_super = super().from_parent
        except AttributeError:  # PyTest < 5.4
            self = cls(name, parent)
        else:
            self = from_parent_super(parent, name=name)
        self._name = getattr(obj, '_mangled_name', name)
        self.funcobj = obj
        return self

    def collect(self):
        self.session._fixturemanager.parsefactories(self)
        return super().collect()

    def _getobj(self):
        return self._importtestmodule()

    def _makeid(self):
        """Magic that makes fixtures local to each scope"""
        return f'{self.parent.nodeid}::{self._name}'

    def _importtestmodule(self):
        """Import a describe block as if it was a module"""
        module = make_module_from_function(self.funcobj)
        self.own_markers = getattr(self.funcobj, 'pytestmark', [])
        return module

    def funcnamefilter(self, name):
        """Treat all nested functions as tests

        We do not require the 'test_' prefix for the specs.
        """
        return not name.startswith('_')

    def classnamefilter(self, name):
        """Don't allow test classes inside describe"""
        return False

    def __repr__(self):
        return f"<{self.__class__.__name__} {self._name!r}>"


def pytest_pycollect_makeitem(collector, name, obj):
    if isinstance(obj, types.FunctionType):
        for prefix in collector.config.getini('describe_prefixes'):
            if obj.__name__.startswith(prefix):
                return DescribeBlock.from_parent(collector, obj)


def pytest_addoption(parser):
    parser.addini("describe_prefixes", type="args", default=("describe",),
                  help="prefixes for Python describe function discovery")
