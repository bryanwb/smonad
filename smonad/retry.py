# -*- coding: utf-8 -*-
# Copyright (c) 2017, Bryan W. Berry <bryan.berry@gmail.com>
# License: BSD New, see LICENSE for details.
"""smonad.retry - helpful utility and decorators for retrying operations."""

import time
from functools import wraps
import sys
from .types import ftry
from .utils import succeeded, print_now


class SystemClock:
    '''
    This is just a wrapper around the built-in time.time that makes it much easier to test 
    this module by mocking out time itself.
    '''
    def __init__(self):
        pass

    def time(self):
        '''Returns value of current UNIX epoch in seconds'''
        return time.time()

    def sleep(self, seconds):
        time.sleep(seconds)


class StoppedClock:
    '''    This class only exists to make it easier to test retries
    '''
    def __init__(self):
        self.times = []

    def set_times(self, times):
        '''list of times for the self.time call to return
        the times can be a single value or be a value + side effect to trigger

        example:
           clock.set_times([100, 200, (300, lambda: Failure("Uh oh!"), 400])

        the 3rd invocation of clock.time() will return the Failure

        example:
           clock.set_times([100, 200, (300, function_with_side_effect), 400])
           
        function_with_side_effect will be triggered the 3rd time clock.time() is invoked
        '''
        self.times = times
        self.current = iter(times)

    def sleep(self, seconds):
        '''This sleep doesn't actually sleep, so your tests run quickly!'''
        pass

    def time(self):
        current_time = self.current.next()
        if not isinstance(current_time, tuple):
            return current_time

        current_time_val, side_effect = current_time
        if isinstance(side_effect, Exception):
            raise side_effect

        side_effect()

        return current_time_val


class TickCounter:

    def __init__(self):
        self.count = 0

    def increment(self):
        self.count += 1
    

clock = SystemClock()


# These are local aliases to the types in smonad
Failure = ftry.Failure
Success = ftry.Success


class NotReady(Failure):
    '''Indicates target is not ready and retryable'''
    pass


def print_start_message(start_message, start_time):
    '''
    Prints a start message and interpolates the start_time if the {start_time} placeholder is 
    present in the message

    example:
       print_start_message("Started operation at {start_time}", start_time)
    '''
    if '{start_time}' in start_message:
        start_message_formatted = start_message.format(start_time=start_time)
        print_now(start_message_formatted)
    else:
        print_now(start_message)


def print_end_message(result, total_time, retry_count):
    sys.stdout.write('\n')
    sys.stdout.flush()

    if not hasattr(result.value, 'format'):
        return

    if succeeded(result):
        print_now(result.value.format(total_time=total_time, retries=retry_count))
    elif isinstance(result, NotReady):
        print_now(result.value.format(total_time=total_time, retries=retry_count) + "  Giving up.", err=True)
    else:
        print_now(result.value.format(total_time=total_time, retries=retry_count), err=True)


def retry(callable_object, timeout=600, delay=4, start_message=None, silent=False):
    """
    Retry calling the decorated function until it returns Success, Failure,
    or the retry count is exceeded
    Values of Success or Failure are returned immediately
    A NotReady means to retry the decorated function permitting that there are remaining retries
    loosely based on:
    http://www.saltycrane.com/blog/2009/11/trying-out-retry-decorator-python/
    original from: http://wiki.python.org/moin/PythonDecoratorLibrary#Retry

    This decorator expects the wrapped function to return any of three types
    Failure, NotReady, or Success
    Note that Failure and Success are imported from smonad.types.ftry and that
    NotReady is a subclass of Failure

    Values of Success or Failure are returned immediately
    A NotReady means to retry the decorated function permitting that there are remaining retries
    
    :param callable_object: object that can be called
    :type callable_object: function
    :param timeout: maximum period, in seconds, to wait until an individual try succeeds
    :type timeout: int
    :param delay: initial delay between retries in seconds
    :type delay: int
    :param start_message: message to print before executing first attempt, may contain placeholder {start_time}
              example `start_message="Started operation at {start_time}"`
    :type start_message: str
    :param silent: do not print start, end, or progress dots
    :type silent: bool
    """
    delay = delay
    start_message = start_message
    
    @wraps(callable_object)
    def f_retry(*args, **kwargs):
        start_time = clock.time()
        deadline = start_time + timeout
        tick_counter = TickCounter()
        current_time = start_time
            
        if start_message and not silent:
            print_start_message(start_message, start_time)

        while current_time < deadline:
            result = callable_object(*args, **kwargs)
            tick_counter.increment()
            if isinstance(result, NotReady):
                # it is a NotReady
                if not silent:
                    sys.stdout.write('.')
                    # after every 80 ticks, print a newline
                    # to avoid running off the screen
                    if tick_counter.count % 80 == 0:
                        sys.stdout.write('\n')
                    sys.stdout.flush()
                clock.sleep(delay)
                current_time = clock.time()
            else:
                break

        total_time = current_time - start_time

        if not silent:
            print_end_message(result, total_time, tick_counter.count)

        if isinstance(result.value, str):
            result.value.format(total_time=total_time, retries=tick_counter.count)

        return result

    return f_retry  # true decorator


def retry_decorator(timeout=600, delay=4, start_message=None, silent=False):
    '''Decorator that wraps a callable with a retry loop. The callable should only return
    :class:Failure, :class:Success, or :class:NotReady

    >>> deadline = time.time() + 300
    >>> @retry_decorator()
    ... def wait_for_deadline():
    ...     now = time.time()
    ...     if now < deadline:
    ...         return NotReady("not ready yet")
    ...     else:
    ...         return Success("Ready!")
    >>> wait_for_deadline()  # doctest: +SKIP
    Success("Ready!")
    '''
    def deco_retry(f):
        return retry(f, timeout=timeout, delay=delay, start_message=start_message, silent=silent)

    return deco_retry
