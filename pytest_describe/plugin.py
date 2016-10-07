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
    for behavior in getattr(funcobj, '_behaves_like', []):
        module.__dict__.update(trace_function(behavior))
    module.__dict__.update(trace_function(funcobj))
    return module


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
        self.funcobj = funcobj

    def collect(self):
        self.session._fixturemanager.parsefactories(self)
        return super(DescribeBlock, self).collect()

    def _getobj(self):
        return self._memoizedcall('_obj', self._importtestmodule)

    def _makeid(self):
        """Magic that makes fixtures local to each scope"""
        return self.parent.nodeid + '::' + self.funcobj.__name__

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
                                repr(self.funcobj.__name__))


def pytest_pycollect_makeitem(collector, name, obj):
    if isinstance(obj, types.FunctionType):
        for prefix in collector.config.getini('describe_prefixes'):
            if obj.__name__.startswith(prefix):
                return DescribeBlock(obj, collector)


def pytest_addoption(parser):
    parser.addini("describe_prefixes", type="args", default=("describe",),
                  help="prefixes for Python describe function discovery")
