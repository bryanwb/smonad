# -*- coding: utf-8 -*-
# Copyright (c) 2012-2014, Philip Xu <pyx@xrefactor.com>
# License: BSD New, see LICENSE for details.
"""smonad.types.ftry - The Try Monad."""

from . import Monad, Monadic
from ..mixins import ContextManager, Ord


class Try(Monad, ContextManager, Ord):
    """The Either Monad by a different name

    Represents values/computations with two possibilities.

    >>> Success(42)
    Success(42)
    >>> Success([1, 2, 3])
    Success([1, 2, 3])
    >>> Failure('Error')
    Failure('Error')
    >>> Success(Failure('Error'))
    Success(Failure('Error'))
    >>> isinstance(Success(1), Try)
    True
    >>> isinstance(Failure(None), Try)
    True
    >>> saving = 100
    >>> broke = Failure('I am broke')
    >>> spend = lambda cost: broke if cost > saving else Success(saving - cost)
    >>> spend(90)
    Success(10)
    >>> spend(120)
    Failure('I am broke')
    >>> safe_div = lambda a, b: Failure(str(a) + '/0') if b == 0 else Success(a / b)
    >>> safe_div(12.0, 6)
    Success(2.0)
    >>> safe_div(12.0, 0)
    Failure('12.0/0')

    Bind operation with ``>>``

    >>> inc = lambda n: Success(n + 1) if type(n) is int else Failure('Type error')
    >>> Success(0)
    Success(0)
    >>> Success(0) >> inc
    Success(1)
    >>> Success(0) >> inc >> inc
    Success(2)
    >>> Success('zero') >> inc
    Failure('Type error')

    Comparison with ``==``, as long as they are the same type and what's
    wrapped inside are comparable.

    >>> Failure(42) == Failure(42)
    True
    >>> Success(42) == Success(42)
    True
    >>> Failure(42) == Success(42)
    False

    A :py:class:`Failure` is less than a :py:class:`Success`, or compare the two by
    the values inside if thay are of the same type.

    >>> Failure(42) < Success(42)
    True
    >>> Success(0) > Failure(100)
    True
    >>> Failure('Error message') > Success(42)
    False
    >>> Failure(100) > Failure(42)
    True
    >>> Success(-2) < Success(-1)
    True
    """
    def __init__(self, value):
        super(Try, self).__init__(value)
        if type(self) is Try:
            raise NotImplementedError('Please use Failure or Success instead')

    def bind(self, function):
        """The bind operation of :py:class:`Try`.

        Applies function to the value if and only if this is a
        :py:class:`Success`.
        """
        return self and function(self.value)

    def __repr__(self):
        """Customize Show."""
        fmt = 'Success({})' if self else 'Failure({})'
        return fmt.format(repr(self.value))

    # Customize Ord logic
    def __lt__(self, monad):
        """Override to handle special case: Success."""
        if not isinstance(monad, (Failure, Success)):
            fmt = "unorderable types: {} and {}'".format
            raise TypeError(fmt(type(self), type(monad)))
        if type(self) is type(monad):
            # same type, either both lefts or rights, compare against value
            return self.value < monad.value
        if monad:
            # self is Failure and monad is Success, left is less than right
            return True
        else:
            return False

    def match(self, failure_handler, right_handler=None):
        """
        Given two mapping functions (one from an Failure to a value, one from a Success to a
        Value), unwrap the value stored in this Try, apply the appropriate
        mapping function, and return the result.

        If the right_handler is None and self is an instance of Success, the wrapped value is returned
        """
        if isinstance(self, Failure):
            return failure_handler(self.value)

        if right_handler is None:
            return self.value

        return right_handler(self.value)

    def recover(self, recovery_fn):
        """
        "Recover" from a left value by applying a recovery_fn to the wrapped
        value and returning it in the case of a left value; otherwise, return
        the wrapped right value.
        """
        if isinstance(self, Failure):
            return recovery_fn(self.value)

        else:
            return self


class Failure(Try):
    """Failure of :py:class:`Try`."""
    def __bool__(self):
        # pylint: disable = no-self-use
        return False
    __nonzero__ = __bool__


class Success(Try):
    """Success of :py:class:`Try`."""


Try.unit = Monadic(Success)
