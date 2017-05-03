import os
import pytest
from smonad import retry
from smonad.utils import succeeded


class ValueHolder:
    '''This class only exists to create a value that can be passed by reference'''
    def __init__(self):
        self.value = False

    def set(self, value):
        self.value = value


def check_value(value_holder):
    if value_holder.value is True:
        return retry.Success("Check succeeded after {total_time} seconds and {retries} retries")
    elif value_holder.value is False:
        return retry.NotReady("Check still not ready after {total_time} seconds and {retries} retries")
    else:
        return retry.Failure("Check failed after {total_time} seconds and {retries} retries")


def test_retry_fails_after_5_times(capsys):
    clock = retry.StoppedClock()
    clock.set_times([200, 250, 300, 350, 500, 600])
    retry.clock = clock
    retry_check_value = retry.retry(check_value, timeout=200)
    result = retry_check_value(ValueHolder())
    assert isinstance(result, retry.NotReady)
    out, err = capsys.readouterr()
    assert '....' in out
    assert 'Check still not ready after 300 seconds and 4 retries  Giving up.' in err


def test_retry_succeed_on_3rd_try(capsys):
    value_holder = ValueHolder()
    clock = retry.StoppedClock()
    clock.set_times([200, 250, (300, lambda: value_holder.set(True)), 350, 500])
    retry.clock = clock
    retry_check_value = retry.retry(check_value, timeout=200)
    result = retry_check_value(value_holder)
    assert isinstance(result, retry.Success)
    out, err = capsys.readouterr()
    assert '..' in out
    assert 'Check succeeded after 100 seconds and 3 retries' in out


def test_retry_not_ready_failure(capsys):
    value_holder = ValueHolder()
    clock = retry.StoppedClock()
    clock.set_times([200, 250, (300, lambda: value_holder.set(None)), 350, 500])
    retry.clock = clock
    retry_check_value = retry.retry(check_value, timeout=200)
    result = retry_check_value(value_holder)
    assert isinstance(result, retry.Failure)
    out, err = capsys.readouterr()
    assert '..' in out
    assert "Check failed after 100 seconds and 3 retries" in err
    

def test_retry_tick_count_wraps(capsys):
    value_holder = ValueHolder()
    clock = retry.StoppedClock()
    clock.set_times(list(xrange(1, 300)))
    retry.clock = clock
    retry_check_value = retry.retry(check_value, timeout=200)
    result = retry_check_value(value_holder)
    assert isinstance(result, retry.NotReady)
    out, err = capsys.readouterr()
    lines = out.strip().split('\n')
    first_line = lines[0]
    second_line = lines[1]
    assert first_line.count('.') == 80
    assert second_line.count('.') == 80


def test_retry_decorator_fails_after_5_times(capsys):
    clock = retry.StoppedClock()
    clock.set_times([200, 250, 300, 350, 500, 600])
    retry.clock = clock

    # this function definition must be inline so that the decorated method
    # closes over our stopped clock
    
    @retry.retry_decorator(timeout=200)
    def decorated_check_value(value_holder):
        if value_holder.value is True:
            return retry.Success("Check succeeded after {total_time} seconds and {retries} retries")
        elif value_holder.value is False:
            return retry.NotReady("Check still not ready after {total_time} seconds and {retries} retries")
        else:
            return retry.Failure("Check failed after {total_time} seconds and {retries} retries")

    result = decorated_check_value(ValueHolder())
    assert isinstance(result, retry.NotReady)
    out, err = capsys.readouterr()
    assert '....' in out
    assert 'Check still not ready after 300 seconds and 4 retries  Giving up.' in err


def test_retry_decorator_succeed_on_3rd_try(capsys):
    value_holder = ValueHolder()
    clock = retry.StoppedClock()
    clock.set_times([200, 250, (300, lambda: value_holder.set(True)), 350, 500])
    retry.clock = clock

    @retry.retry_decorator(timeout=200)
    def decorated_check_value(value_holder):
        if value_holder.value is True:
            return retry.Success("Check succeeded after {total_time} seconds and {retries} retries")
        elif value_holder.value is False:
            return retry.NotReady("Check still not ready after {total_time} seconds and {retries} retries")
        else:
            return retry.Failure("Check failed after {total_time} seconds and {retries} retries")

    result = decorated_check_value(value_holder)
    assert succeeded(result)
    out, err = capsys.readouterr()
    assert '..' in out
    assert 'Check succeeded after 100 seconds and 3 retries' in out


@pytest.fixture
def datadir():
    '''This fixture returns the path to the directory holding helper files'''
    return os.path.join(os.path.dirname(__file__), "data")
