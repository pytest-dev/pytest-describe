import sys
import types
from _pytest.python import PyCollector


def trace_function(funcobj, *args, **kwargs):
    """Call a function, and return its locals"""
    funclocals = {}

    def _tracefunc(frame, event, arg):
        # Activate local trace for first call only
        if frame.f_back.f_locals.get('_tracefunc') == _tracefunc:
            if event == 'return':
                funclocals.update(frame.f_locals)

    sys.setprofile(_tracefunc)
    try:
        funcobj(*args, **kwargs)
    finally:
        sys.setprofile(None)

    return funclocals


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
