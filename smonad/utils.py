# -*- coding: utf-8 -*-
# Copyright (c) 2012-2014, Philip Xu <pyx@xrefactor.com>
# License: BSD New, see LICENSE for details.
"""monad.utils - utility functions and values."""

from collections import Iterable


def succeeded(obj):
    """Return a Boolean that indicates if the value is an instance of smonad.types.ftry.Success

    >>> from smonad.types.ftry import Failure, Success
    >>> succeeded(Success(True))
    True
    >>> succeeded(Failure('fubar'))
    False
    """
    # import inside the function to avoid circular module dependencies
    from smonad.types.ftry import Try, Success
    assert isinstance(obj, Try)
    return isinstance(obj, Success)


def failed(obj):
    """Return a Boolean that indicates if the value is an instance of smonad.types.ftry.Failure

    >>> from smonad.types.ftry import Failure, Success
    >>> failed(Failure('shit is fucked up'))
    True
    >>> failed(Success('it worked!'))
    False
    """
    # import inside the function to avoid circular module dependencies
    from smonad.types.ftry import Try, Failure
    assert isinstance(obj, Try)
    return isinstance(obj, Failure)


# cannot wait for python 3.4, also do a type-check here
class SuppressContextManager(object):
    """Context manager class that suppress specified exceptions."""
    # pylint: disable = too-few-public-methods
    def __init__(self, *exceptions):
        # except accepts exception or expects exceptions in tuple. :p
        invalid_args = (
            not isinstance(ex, type) or not issubclass(ex, BaseException)
            for ex in exceptions)
        if any(invalid_args):
            raise TypeError('argument must be a subclass of BaseException')

        self.exceptions = exceptions

    def __enter__(self):
        pass

    def __exit__(self, exc_type, exc_val, exc_tb):
        if isinstance(exc_val, self.exceptions):
            return True
        return False


def suppress(*exceptions):
    """Context manager that suppress specified exceptions.

    >>> with suppress(ZeroDivisionError):
    ...     42 / 0
    """
    return SuppressContextManager(*exceptions)


def compose(f, g):
    """Function composition.

    ``compose(f, g) -> f . g``

    >>> add_2 = lambda a: a + 2
    >>> mul_5 = lambda a: a * 5
    >>> mul_5_add_2 = compose(add_2, mul_5)
    >>> mul_5_add_2(1)
    7
    >>> add_2_mul_5 = compose(mul_5, add_2)
    >>> add_2_mul_5(1)
    15
    """
    # pylint: disable = invalid-name, star-args
    return lambda *args, **kwargs: f(g(*args, **kwargs))


def identity(a):
    """Identity function."""
    # pylint: disable = invalid-name
    return a


def ignore_exception_set(*exceptions):
    """Helper function for suppress."""
    to_be_ignored = set()
    for exception in exceptions:
        if not exception:
            continue
        if not isinstance(exception, Iterable):
            exception = (exception,)
        to_be_ignored |= set(exception)
    return to_be_ignored
