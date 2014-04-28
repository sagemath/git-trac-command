"""
Python 2.6 hacks
"""


import sys
import subprocess


########################################################################################

def check_output(*popenargs, **kwargs):
    """
    Emulation of check_output
    """
    if 'stdout' in kwargs:
        raise ValueError('stdout argument not allowed, it will be overridden.')
    process = subprocess.Popen(stdout=subprocess.PIPE, *popenargs, **kwargs)
    output, unused_err = process.communicate()
    retcode = process.poll()
    if retcode:
        cmd = kwargs.get("args")
        if cmd is None:
            cmd = popenargs[0]
        raise subprocess.CalledProcessError(retcode, cmd)
    return output


########################################################################################
# Backport of importlib.import_module from 3.x.
#
# Code from: http://code.activestate.com/recipes/576685/

def total_ordering(cls):
    """
    Backport to work with Python 2.6

    Class decorator that fills in missing ordering methods
    """
    convert = {
        '__lt__': [
            (
                '__gt__',
                lambda self, other: not (self < other or self == other)
            ),
            (
                '__le__',
                lambda self, other: self < other or self == other
            ),
            (
                '__ge__',
                lambda self, other: not self < other
            )],
        '__le__': [
            (
                '__ge__',
                lambda self, other: not self <= other or self == other
            ),
            (
                '__lt__',
                lambda self, other: self <= other and not self == other
            ),
            (
                '__gt__',
                lambda self, other: not self <= other
            )],
        '__gt__': [
            (
                '__lt__',
                lambda self, other: not (self > other or self == other)
            ),
            (
                '__ge__',
                lambda self, other: self > other or self == other
            ),
            (
                '__le__',
                lambda self, other: not self > other
            )],
        '__ge__': [
            (
                '__le__',
                lambda self, other: (not self >= other) or self == other
            ),
            (
                '__gt__',
                lambda self, other: self >= other and not self == other
            ),
            (
                '__lt__',
                lambda self, other: not self >= other
            )]
    }
    roots = set(dir(cls)) & set(convert)
    if not roots:
        raise ValueError(
            'must define at least one ordering operation: < > <= >='
        )
    root = max(roots)       # prefer __lt__ to __le__ to __gt__ to __ge__
    for opname, opfunc in convert[root]:
        if opname not in roots:
            opfunc.__name__ = opname
            opfunc.__doc__ = getattr(int, opname).__doc__
            setattr(cls, opname, opfunc)
    return cls



########################################################################################
# Backport of importlib.import_module from 3.x.
#
# Taken from https://pypi.python.org/pypi/importlib

def _resolve_name(name, package, level):
    """Return the absolute name of the module to be imported."""
    if not hasattr(package, 'rindex'):
        raise ValueError("'package' not set to a string")
    dot = len(package)
    for x in xrange(level, 1, -1):
        try:
            dot = package.rindex('.', 0, dot)
        except ValueError:
            raise ValueError("attempted relative import beyond top-level "
                              "package")
    return "%s.%s" % (package[:dot], name)


def import_module(name, package=None):
    """Import a module.

    The 'package' argument is required when performing a relative import. It
    specifies the package to use as the anchor point from which to resolve the
    relative import to an absolute import.

    """
    if name.startswith('.'):
        if not package:
            raise TypeError("relative imports require the 'package' argument")
        level = 0
        for character in name:
            if character != '.':
                break
            level += 1
        name = _resolve_name(name[level:], package, level)
    __import__(name)
    return sys.modules[name]
