# -*- coding: utf-8 -*-
# Copyright (c) 2012-2014, Philip Xu <pyx@xrefactor.com>
# License: BSD New, see LICENSE for details.
import pytest

from smonad.actions import ftry
from smonad.decorators import failsafe
from smonad.exceptions import ExtractError
from smonad.types import Try, Failure, Success


test_range = range(-100, 100)
unit = Try.unit

error = Failure('Error')


def add_1(n):
    if isinstance(n, int):
        return unit(n + 1)
    else:
        return error


def double(n):
    if isinstance(n, int):
        return unit(n * 2)
    else:
        return error


def fail(n):
    return error


def test_local_helper_function_add_one():
    for n in test_range:
        assert add_1(n) == unit(n + 1)
    assert add_1('1') is error


def test_local_helper_function_double():
    for n in test_range:
        assert double(n) == unit(n * 2)
    assert double('1') is error


def test_local_helper_function_fail():
    for n in test_range:
        assert fail(n) is error


def test_fmap_functor_laws():
    identity = lambda a: a
    f = lambda a: a + 1
    g = lambda a: a * 2
    f_g = lambda n: f(g(n))

    for n in test_range:
        ft = unit(n)
        # fmap id == id
        assert ft.fmap(identity) == identity(ft)
        # fmap (f . g) == fmap f . fmap g
        assert ft.fmap(f_g) == ft.fmap(g).fmap(f)

    value = 42
    l = Failure('Something wrong.')
    r = Success(value)
    assert l.fmap(f) is l
    assert r.fmap(f) == Success(f(42))


def test_unit():
    assert type(unit(42)) is Success


def test_ftry_is_abstract():
    with pytest.raises(NotImplementedError):
        Try(42)


def test_compare():
    for n in test_range:
        assert Failure(n) == Failure(n)
        assert Success(n) == Success(n)
        assert Failure(n) != Success(n)


def test_ordering():
    with pytest.raises(TypeError):
        Failure(1) < 1

    with pytest.raises(TypeError):
        Success(1) < 1

    for n in test_range:
        assert (Failure(n) < Failure(n)) is False
        assert Failure(n) > Failure(n - 1)
        assert Failure(n) < Failure(n + 1)
        assert (Success(n) < Success(n)) is False
        assert Success(n) > Success(n - 1)
        assert Success(n) < Success(n + 1)
        assert Failure(n) < Success(n)


def test_as_context_manager():
    for n in test_range:
        with pytest.raises(ExtractError):
            with unit(n) >> double >> fail >> double as result:
                assert False
                assert result

    with pytest.raises(ExtractError):
        with error as n:
            assert False

    with pytest.raises(ExtractError):
        with double(n) as result:
            with error as n:
                assert False

    with pytest.raises(ExtractError):
        with double(n) as result, error as n:
            assert False


def test_bool():
    assert bool(Failure(True)) is False
    assert bool(Success(False)) is True
    for n in test_range:
        assert bool(Failure(n)) is False
        assert bool(Success(n)) is True
        assert bool(unit(n)) is True


def test_bind():
    assert error.bind(add_1) is error
    for n in test_range:
        m = unit(n)
        assert m.bind(fail) is error


def test_bind_operator():
    for n in test_range:
        m = unit(n)
        assert m >> fail is error
        assert fail(n) >> add_1 is error


def test_reversed_bind_operator():
    for n in test_range:
        m = unit(n)
        assert fail << m is error
        assert add_1 << fail(n) is error


def test_chain_bind_operator():
    for n in test_range:
        m = unit(n)
        assert m >> fail >> add_1 == error
        assert m >> add_1 >> fail == error
        assert m >> fail >> double == error
        assert m >> double >> fail == error


def test_monad_law_left_identity():
    for n in test_range:
        # unit n >>= f == f n
        f = fail
        assert unit(n) >> f == f(n)


def test_monad_law_right_identity():
    for n in test_range:
        # m >>= unit == m
        assert error >> unit == error


def test_monad_law_associativity():
    for n in test_range:
        # m >>= (\x -> k x >>= h)  ==  (m >>= k) >>= h
        m = unit(n)
        k = add_1
        h = fail
        assert m >> (lambda x: k(x) >> h) == (m >> k) >> h
        k = fail
        h = double
        assert m >> (lambda x: k(x) >> h) == (m >> k) >> h
        k = fail
        h = fail
        assert m >> (lambda x: k(x) >> h) == (m >> k) >> h


def test_ftry_action():
    inc = lambda n: n + 1
    dec = lambda n: n - 1

    act = ftry(inc)
    assert act(Failure(1)) == 2
    assert act(Success(1)) == 1

    act = ftry(failure_handler=inc, success_handler=dec)
    assert act(Failure(1)) == 2
    assert act(Success(1)) == 0


def test_ftry_action_with_incompatible_type():
    inc = lambda n: n + 1

    act = ftry(inc)
    assert act(Failure(1)) == 2

    with pytest.raises(TypeError):
        act(1)


def test_failsafe_decorator():
    @failsafe
    def div(a, b):
        return a / b

    assert div(42, 21) == unit(2)
    assert isinstance(div(42, 0), Failure)


def test_failsafe_decorator_catch_extract_error():
    @failsafe(failure_on_exception=None)
    def wrong():
        with fail(1) as result:
            assert result is False  # should not reach here

    assert wrong() == error

    @failsafe(failure_on_exception=None)
    def wrong():
        raise ExtractError('not a left')

    assert isinstance(wrong(), Failure)


def test_failsafe_decorator_with_predicate():
    @failsafe(predicate=bool)
    def truth(x):
        return x

    assert truth(42) == unit(42)
    assert truth(None) == Failure(None)
    assert add_1(0) >> truth == unit(1)
    assert add_1(-1) >> truth == Failure(0)
    assert truth(False) >> double == Failure(False)
    assert double([]) >> truth == error


def test_failsafe_decorator_with_value():
    @failsafe(failure_on_value=None)
    def truth(x):
        return x

    assert truth(42) == unit(42)
    assert truth('') == unit('')
    assert truth(0) == unit(0)
    assert truth(False) == unit(False)
    assert truth(None) == Failure(None)


def test_failsafe_decorator_combined():
    @failsafe(predicate=bool, failure_on_value=42)
    def wrap(x):
        return x

    assert wrap(True) == Success(True)
    assert wrap(False) == Failure(False)
    assert wrap('something') == Success('something')
    assert wrap('') == Failure('')
    assert wrap([False]) == Success([False])
    assert wrap([]) == Failure([])
    assert wrap(1) == Success(1)
    assert wrap(0) == Failure(0)
    assert wrap(None) == Failure(None)
    assert wrap(42) == Failure(42)


def test_failsafe_decorator_none_exception():
    @failsafe(failure_on_exception=None)
    def div(a, b):
        return a / b

    with pytest.raises(ZeroDivisionError):
        div(42, 0)


def test_failsafe_decorator_empty_seq_exception():
    for empty in ([], tuple(), set()):
        @failsafe(failure_on_exception=empty)
        def div(a, b):
            return a / b

        with pytest.raises(ZeroDivisionError):
            div(42, 0)


def test_failsafe_decorator_specific_exception():
    @failsafe(failure_on_exception=ZeroDivisionError)
    def div(a, b):
        return a / b

    assert isinstance(div(42, 0), Failure)


def test_failsafe_decorator_specific_exception_tuple():
    @failsafe(failure_on_exception=(IOError, ZeroDivisionError))
    def div(a, b):
        if a < 0:
            raise IOError
        return a / b

    assert isinstance(div(42, 0), Failure)
    assert isinstance(div(-42, 2), Failure)


def test_match_failure_only():
    assert Failure(0).match(lambda v: v + 1) == 1
    assert Success(10).match(lambda v: v + 1) == 10


def test_match_failure_and_success():
    assert Failure(0).match(lambda v: v + 1, lambda v: v / 2) == 1
    assert Success(10).match(lambda v: v + 1, lambda v: v / 2) == 5


def test_recover():
    result = Failure(0).recover(lambda v: v + 1)
    assert result == 1
    
    result = Success(10).recover(lambda v: v + 1)
    assert isinstance(result, Success)
    assert result.value == 10

