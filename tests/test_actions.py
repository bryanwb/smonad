from smonad.types.ftry import Success, Failure
from smonad import actions
import pytest


def test_attempt_failure():
    result = actions.attempt(lambda: 1 / 0, exception=ZeroDivisionError)
    assert isinstance(result, Failure)
    assert isinstance(result.value, ZeroDivisionError)
    assert result.value.message == "integer division or modulo by zero"


def test_attempt_failure_catch_all():
    result = actions.attempt(lambda: 1 / 0)
    assert isinstance(result, Failure)
    assert isinstance(result.value, ZeroDivisionError)
    assert result.value.message == "integer division or modulo by zero"


def test_attempt_failure_wrong_exception():
    with pytest.raises(ZeroDivisionError):
        actions.attempt(lambda: 1 / 0, exception=ValueError)


def test_attempt():
    result = actions.attempt(lambda: 1 / 1)
    assert isinstance(result, Success)
    assert result.value == 1


