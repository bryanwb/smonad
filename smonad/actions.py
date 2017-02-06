# -*- coding: utf-8 -*-
# Copyright (c) 2012-2014, Philip Xu <pyx@xrefactor.com>
# License: BSD New, see LICENSE for details.
"""smonad.actions - useful monadic actions."""

from .decorators import function, monadic
from .types import Try, Failure, Success
from .types import Just, Nothing
from .utils import identity
import StringIO
import sys
import traceback


def _get_stacktrace():
    t, _, tb = sys.exc_info()
    f = StringIO.StringIO()
    traceback.print_tb(tb, None, f)
    stacktrace = f.getvalue()
    return stacktrace


def attempt(callable, exception=None):
    """Call callable and wrap it with appropriate Failure or Success

    If calling the callable raises an exception, wrap the exception in a Failure.
    If the keyword argument ``exception`` is not None, only wrap
    the specified exception. Raise all other exceptions.
    The stacktrace related to the exception is added to the wrapped exception
    as the `stractrace` property

    If the calling the callable does not raise an exception, return Success 
    wrapping the value
    """
    if exception is None:
        catch_exception = Exception
    else:
        catch_exception = exception

    try:
        value = callable()
        return Success(value)
    except catch_exception as e:
        stacktrace = _get_stacktrace()
        e.stacktrace = stacktrace
        return Failure(e)
    
    
@function
def ftry(failure_handler, success_handler=identity):
    """Case analysis for ``Try``.

    This function is named ftry instead of try to avoid collision with the ``try`` keyword.

    Returns a function that when called with a value of type ``Try``,
    applies either ``failure_handler`` or ``success_handler`` to that value
    depending on the type of it.  If an incompatible value is passed, a
    ``TypeError`` will be raised.

    >>> def log(v):
    ...     print('Got Failure({})'.format(v))
    >>> logger = ftry(failure_handler=log)
    >>> logger(Failure(1))
    Got Failure(1)
    >>> logger(Success(1))
    1
    >>> def inc(v):
    ...     return v + 1
    >>> act = ftry(log, inc)
    >>> [act(v) for v in (Failure(0), Success(1), Failure(2), Success(3))]
    Got Failure(0)
    Got Failure(2)
    [None, 2, None, 4]
    """
    @function
    def analysis(a_try):
        """Apply handler functions based on value."""
        aug_type = type(a_try)
        if not issubclass(aug_type, Try):
            raise TypeError(
                'applied either on incompatible type: %s' % aug_type)
        if issubclass(aug_type, Failure):
            return failure_handler(a_try.value)
        assert issubclass(aug_type, Success)
        return success_handler(a_try.value)
    return analysis


@function
def tryout(*functions):
    """Combine functions into one.

    Returns a monadic function that when called, will try out functions in
    ``functions`` one by one in order, testing the result, stop and return
    with the first value that is true or the last result.

    >>> zero = lambda n: 'zero' if n == 0 else False
    >>> odd = lambda n: 'odd' if n % 2 else False
    >>> even = lambda n: 'even' if n % 2 == 0 else False
    >>> test = tryout(zero, odd, even)
    >>> test(0)
    'zero'
    >>> test(1)
    'odd'
    >>> test(2)
    'even'
    """
    @monadic
    def trying(*args, **kwargs):
        """Monadic function that try out functions in order."""
        last = None
        for func in functions:
            last = func(*args, **kwargs)
            if last:
                break
        return last
    return trying


@monadic
def first(sequence, default=Nothing, predicate=None):
    """Iterate over a sequence, return the first ``Just``.

    If ``predicate`` is provided, ``first`` returns the first item that
    satisfy the ``predicate``, the item will be wrapped in a :class:`Just` if
    it is not already, so that the return value of this function will be an
    instance of :class:`Maybe` in all circumstances.
    Returns ``default`` if no satisfied value in the sequence, ``default``
    defaults to :data:`Nothing`.

    >>> from smonad.types import Just, Nothing
    >>> first([Nothing, Nothing, Just(42), Nothing])
    Just(42)
    >>> first([Just(42), Just(43)])
    Just(42)
    >>> first([Nothing, Nothing, Nothing])
    Nothing
    >>> first([])
    Nothing
    >>> first([Nothing, Nothing], default=Just(2))
    Just(2)
    >>> first([False, 0, True], predicate=bool)
    Just(True)
    >>> first([False, 0, Just(1)], predicate=bool)
    Just(1)
    >>> first([False, 0, ''], predicate=bool)
    Nothing
    >>> first(range(100), predicate=lambda x: x > 40 and x % 2 == 0)
    Just(42)
    >>> first(range(100), predicate=lambda x: x > 100)
    Nothing

    This is basically a customized version of ``msum`` for :class:`Maybe`,
    a separate function like this is needed because there is no way to write a
    generic ``msum`` in python that cab be evaluated in a non-strict way.
    The obvious ``reduce(operator.add, sequence)``, albeit beautiful, is
    strict, unless we build up the sequence with generator expressions
    in-place.

    Maybe (pun intended!) implemented as ``MonadOr`` instead of ``MonadPlus``
    might be more semantically correct in this case.
    """
    if predicate is None:
        predicate = lambda m: m and isinstance(m, Just)

    for item in sequence:
        if predicate(item):
            if not isinstance(item, Just):
                item = Just(item)
            return item
    return default


# As decorators function and monadic turn decorated functions into Function
# and Monadic instance objects, respectively, doctest will ignore docstring in
# them, the following adds those docstring into testsuite back again,
# explicitly.
__test__ = {
    'attempt': ftry.__doc__,
    'ftry': ftry.__doc__,
    'tryout': tryout.__doc__,
    'first': first.__doc__,
}
