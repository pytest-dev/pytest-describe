import imp
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
                funclocals.update(frame.f_locals.copy())

    sys.setprofile(_tracefunc)
    try:
        funcobj(*args, **kwargs)
    finally:
        sys.setprofile(None)

    return funclocals


def make_module_from_function(funcobj):
    """Evaluates the local scope of a function, as if it was a module"""
    module = imp.new_module(funcobj.__name__)

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
                name = obj._mangled_name = "{}::{}".format(funcobj.__name__, name)

            funcobj._shared_functions[name] = obj
    return funcobj._shared_functions


def copy_markinfo(module, funcobj):
    from _pytest.mark import MarkInfo

    marks = {}
    for name, val in funcobj.__dict__.items():
        if isinstance(val, MarkInfo):
            marks[name] = val

    for obj in module.__dict__.values():
        if isinstance(obj, types.FunctionType):
            for name, mark in marks.items():
                setattr(obj, name, mark)


def merge_pytestmark(module, parentobj):
    try:
        pytestmark = parentobj.pytestmark
        if not isinstance(pytestmark, list):
            pytestmark = [pytestmark]
        try:
            if isinstance(module.pytestmark, list):
                pytestmark.extend(module.pytestmark)
            else:
                pytestmark.append(module.pytestmark)
        except AttributeError:
            pass
        module.pytestmark = pytestmark
    except AttributeError:
        pass


class DescribeBlock(PyCollector):
    """Module-like object representing the scope of a describe block"""

    def __init__(self, funcobj, parent):
        super(DescribeBlock, self).__init__(funcobj.__name__, parent)
        self._name = getattr(funcobj, '_mangled_name', funcobj.__name__)
        self.funcobj = funcobj

    def collect(self):
        self.session._fixturemanager.parsefactories(self)
        return super(DescribeBlock, self).collect()

    def _getobj(self):
        return self._memoizedcall('_obj', self._importtestmodule)

    def _makeid(self):
        """Magic that makes fixtures local to each scope"""
        return self.parent.nodeid + '::' + self._name

    def _importtestmodule(self):
        """Import a describe block as if it was a module"""
        module = make_module_from_function(self.funcobj)
        copy_markinfo(module, self.funcobj)
        merge_pytestmark(module, self.parent.obj)
        return module

    def funcnamefilter(self, name):
        """Treat all nested functions as tests, without requiring the 'test_' prefix"""
        return not name.startswith('_')

    def classnamefilter(self, name):
        """Don't allow test classes inside describe"""
        return False

    def __repr__(self):
        return "<{} {}>".format(self.__class__.__name__,
                                repr(self._name))


def pytest_pycollect_makeitem(collector, name, obj):
    if isinstance(obj, types.FunctionType):
        for prefix in collector.config.getini('describe_prefixes'):
            if obj.__name__.startswith(prefix):
                return DescribeBlock(obj, collector)


def pytest_addoption(parser):
    parser.addini("describe_prefixes", type="args", default=("describe",),
                  help="prefixes for Python describe function discovery")
