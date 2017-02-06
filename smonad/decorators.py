# -*- coding: utf-8 -*-
# Copyright (c) 2012-2014, Philip Xu <pyx@xrefactor.com>
# License: BSD New, see LICENSE for details.
"""smonad.decorators - helpful decorators."""

from functools import partial, wraps

from .exceptions import ExtractError
from .types import Null
from .types import Function
from .types import Monadic
from .types import Just, Nothing
from .types import Failure, Success
from .types import List
from .utils import ignore_exception_set, suppress


def function(callable_object):
    """Decorator that wraps a callabe into :class:`Function`.

    >>> to_int = function(int)
    >>> to_int('42')
    42
    >>> @function
    ... def puts(msg, times=1):
    ...     while times > 0:
    ...         print(msg)
    ...         times -= 1
    >>> puts('Hello, world', 2)
    Hello, world
    Hello, world
    """
    return Function(callable_object)


def monadic(callable_object):
    """Decorator that wraps a callabe into :class:`Monadic`."""
    return Monadic(callable_object)


def maybe(callable_object=None,
          predicate=None,
          nothing_on_value=Null,
          nothing_on_exception=Exception):
    """Transform a callable into a function returns a :py:class:`Maybe`.

    >>> parse_int = maybe(int)
    >>> parse_int(42)
    Just(42)
    >>> parse_int(42.0)
    Just(42)
    >>> parse_int('42')
    Just(42)
    >>> parse_int('invalid')
    Nothing

    >>> parse_pos = maybe(int, predicate=lambda i: i > 0)
    >>> parse_pos('42')
    Just(42)
    >>> parse_pos('-42')
    Nothing

    >>> parse_nonzero = maybe(int, nothing_on_value=0)
    >>> parse_nonzero('42')
    Just(42)
    >>> parse_nonzero('0')
    Nothing

    >>> @maybe(nothing_on_exception=ZeroDivisionError)
    ... def safe_div(a, b):
    ...     return a / b
    >>> safe_div(42.0, 2)
    Just(21.0)
    >>> safe_div(42, 0)
    Nothing

    When invoked, this new function returns the return value of decorated
    function, wrapped in a :py:class:`Maybe` monad.

    ``predicate`` should be a false value, or be set to a callable.
    The default is ``None``.

    ``nothing_on_value`` can be set to any object supporting comparison
    against return value of the original function.
    The default is ``Null``, which means no checking on the return value.

    ``nothing_on_exception`` can be a false value, a type of exception, or a
    tuple of exceptions.
    The default is ``Exception``, which will suppress most exceptions and
    return ``Nothing`` instead.


    The returned monad will be ``Nothing`` if

    - ``predicate`` is set, and ``predicate(result_from_decorated_function)``
      returns true value (not necessarily equal to ``True``)
    - ``nothing_on_value`` is set and the result from decorated function
      matches it, testing with ``==``
    - ``nothing_on_exception`` is set and a compatible exception has been
      caught, the exception will be suppressed in this case
    - exception ``ExtractError`` has been caught, when trying to extract value
      from ``Nothing``
    - any combination of the above

    Otherwise, the result will be wrapped in a :py:class:`Just`.
    """
    if callable_object is None:
        return partial(maybe,
                       predicate=predicate,
                       nothing_on_value=nothing_on_value,
                       nothing_on_exception=nothing_on_exception)

    exceptions = ignore_exception_set(ExtractError, nothing_on_exception)

    @wraps(callable_object)
    def wrapper(*args, **kwargs):
        """Monadic function wrapper for Maybe"""
        # pylint: disable = star-args
        with suppress(*exceptions):
            result = callable_object(*args, **kwargs)
            if nothing_on_value is not Null and result == nothing_on_value:
                return Nothing
            if predicate is not None and not predicate(result):
                return Nothing
            return Just(result)
        return Nothing
    return monadic(wrapper)


def failsafe(callable_object=None,
             predicate=None,
             failure_on_value=Null,
             failure_on_exception=Exception):
    """Transform a callable into a function returns an :py:class:`Try`.

    >>> parse_int = failsafe(int)
    >>> parse_int(42)
    Success(42)
    >>> parse_int(42.0)
    Success(42)
    >>> parse_int('42')
    Success(42)
    >>> parse_int('invalid')
    Failure(ValueError(...))

    >>> parse_pos = failsafe(int, predicate=lambda i: i > 0)
    >>> parse_pos('42')
    Success(42)
    >>> parse_pos('-42')
    Failure(-42)

    >>> parse_nonzero = failsafe(int, failure_on_value=0)
    >>> parse_nonzero('42')
    Success(42)
    >>> parse_nonzero('0')
    Failure(0)

    >>> @failsafe(failure_on_exception=ZeroDivisionError)
    ... def safe_div(a, b):
    ...     return a / b
    >>> safe_div(42.0, 2)
    Success(21.0)
    >>> safe_div(42, 0)
    Failure(ZeroDivisionError(...))

    When invoked, this new function returns the return value of decorated
    function, wrapped in an :py:class:`Either` monad.

    ``predicate`` should be a false value, or be set to a callable.
    The default is ``None``.

    ``failure_on_value`` can be set to any object supporting comparison against
    return value of the original function.
    The default is ``Null``, which means no checking on the return value.

    ``failure_on_exception`` should be a false value, or a type of exception,
    or a tuple of exceptions.
    The default is ``Exception``, which will suppress most exceptions and
    return ``Failure(exception)`` instead.

    The returned monad will be :py:class:`Failure` if

    - ``predicate`` is set, and ``predicate(result_from_decorated_function)``
      returns true value (not necessarily equal to ``True``)
    - ``failure_on_value`` is set and the result from decorated function matches
      it, testing with ``==``
    - ``failure_on_exception`` is set and a compatible exception has been caught,
      the exception will be suppressed in this case, and the value of
      exception will be wrapped in a :py:class:`Failure`
    - exception ``ExtractError`` has been caught, this could be the case, for
      example, trying to extract value from ``Nothing``
    - any combination of the above

    Otherwise, the result will be wrapped in a :py:class:`Success`.
    """
    if callable_object is None:
        return partial(failsafe,
                       predicate=predicate,
                       failure_on_value=failure_on_value,
                       failure_on_exception=failure_on_exception)

    exceptions = ignore_exception_set(failure_on_exception)

    @wraps(callable_object)
    def wrapper(*args, **kwargs):
        """Monadic function wrapper for Either"""
        try:
            result = callable_object(*args, **kwargs)
            if failure_on_value is not Null and result == failure_on_value:
                return Failure(result)
            if predicate is not None and not predicate(result):
                return Failure(result)
            return Success(result)
        except ExtractError as ex:
            monad = ex.monad
            if isinstance(monad, Failure):
                return ex.monad
            else:
                return Failure(ex)
        except tuple(exceptions) as ex:
            return Failure(ex)
    return monadic(wrapper)


def producer(function_or_generator=None,
             empty_on_exception=None):
    """Transform a callable into a producer that when called, returns ``List``.

    >>> @producer
    ... def double(a):
    ...     yield a
    ...     yield a
    >>> List(42) >> double
    List(42, 42)

    >>> @producer
    ... def times(a):
    ...     for b in List(1, 2, 3):
    ...         yield '{}x{}={}'.format(a, b, a * b)
    >>> List(1, 2) >> times
    List('1x1=1', '1x2=2', '1x3=3', '2x1=2', '2x2=4', '2x3=6')

    ``function_or_generator`` can be a function that returns an iterable, or a
    generator.

    ``empty_on_exception`` can be a false value, a type of exception, or a
    tuple of exceptions.
    The default is ``None``, which will not suppress all exceptions except
    ``ExtractError``, in which case, an empty :py:class:`List` will be
    returned.
    """
    if function_or_generator is None:
        return partial(producer, empty_on_exception=empty_on_exception)

    exceptions = ignore_exception_set(ExtractError, empty_on_exception)

    @wraps(function_or_generator)
    def wrapper(*args, **kwargs):
        """Monadic function wrapper for List"""
        # pylint: disable = star-args
        with suppress(*exceptions):
            return List.from_iterable(function_or_generator(*args, **kwargs))
        return List.zero
    return monadic(wrapper)
