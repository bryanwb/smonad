======================================================================
smonad - a functional python package with some scala inspiration
======================================================================


Introduction
============


What?
-----

Monads in python, with some helpful functions.

This package is a fork of Philip Xu's excellent `monad package <https://github.com/pyx/monad>`_.
Philip's package has been modified to be more approachable for Python developers. It
takes some inspiration from the excellent `lambda <https://github.com/palatable/lambda>`_ library
for Java and Scala's `Try monad <http://danielwestheide.com/blog/2012/12/26/the-neophytes-guide-to-scala-part-6-error-handling-with-try.html>`_

Python developers may find the Try monad particularly useful as it allows you to treat errors
as values.


Why?
----

Python does not have a good builtin conventions for processing multiple
operations in batch. Further, this library's authors found excessive reliance
on classes can lead to less composable code.

This library borrows some ideas from Haskell and other functional programming
language to better handle the aforementioned use case. While this library does
have 'monad' in its name, you do not need to know anything about the
concept of monads in order to use this library.


Treating Errors as Values
------------------------------

Python does not have a built-in convention for treating errors as values
other than try/except.

smonad introduces the Failure/Success convention of wrapping failed or
successful results in a container class.


The utility method ``attempt`` executes a callable and wraps a raised exception
in a Failure class. If an exception was not raised, a Success is returned

::

  >>> from smonad.actions import attempt
  >>> result = attempt(lambda: 1 / 0)
  >>> print result
  Failure(ZeroDivisionError('integer division or modulo by zero',))
  >>> exc = result.value
  >>> exc
  ZeroDivisionError('integer division or modulo by zero',)
  >>> # the following would fail as it does not catch the correct exception
  >>> # result = attempt(lambda: 1 / 0, exception=ValueError)
  >>> result = attempt(lambda: 1 / 1)
  >>> print result
  Success(1)
  >>> result.value
  1


You can instantiate Failure or Success inside your own code to indicate
whether a computation was successful.


Here is an example script to create AWS instances that uses Failure/Success
to propagate failures to the highest possible level.


::
   
  from collections import namedtuple
  from smonad.types.ftry import Success, Failure
  from smonad.utils import failed
  import sys
  import os


  CloudInstance = namedtuple('CloudInstance', ['name', 'provider', 'instance_type'])

  jenkins = CloudInstance(name='jenkins', provider='aws', instance_type='m3.medium')

  git = CloudInstance(name='git', provider='aws', instance_type='m3.xlarge')

  vault = CloudInstance(name='vault', provider='aws', instance_type='m3.xlarge')


  class TryAgainLaterError(Exception):
      pass


  def aws_create_instance(instance):
      if instance.name == 'jenkins':
          raise TryAgainLaterError("Can't create jenkins server right now")

      return instance


  def create_cloud_instance(instance):
      try:
          created_instance = aws_create_instance(instance)
          return Success(created_instance)
      except TryAgainLaterError as e:
          return Failure(instance)


  def make_my_servers():
      server_results = []
      for server in [jenkins, git, vault]:
          server_results.append(create_cloud_instance(server))

      # if there are any errors, let's retry once more
      failed_servers = filter(lambda r: failed(r), server_results)
      retry_results = []
      for exc, instance in failed_servers:
          retry_results.append(aws_create_instance(instance))

      if any([failed(i) for i in retry_results]):
          failed_servers = ",".join([i.value.name for i in retry_results if failed(i)])
          return Failure("Unable to create servers: %s" % failed_servers)

      return Success("Successfully created all servers")


  if __name__ == "__main__":
      result = make_my_servers()
      if failed(result):
          sys.stderr.write("Error: %s\n" % result.value)
          os.sys.exit(1)
      else:
          print result.value


We can simplify the ``make_my_servers`` function by taking advantage
of the ``recover`` method of ``Try``. recover applies a recovery function
to instances of Failure. It returns Success(V) unchanged.

::

   
  def make_my_servers():
      server_results = []
      for server in [jenkins, git, vault]:
          server_results.append(create_cloud_instance(server))


      # The recover only applies ``create_cloud_instance`` to Failures, it returns the Success value otherwise
      server_results = map(lambda s: s.recover(create_cloud_instance), server_results)

      if any([failed(s) for s in server_results]):
          failed_servers = ",".join([i.value.name for i in server_results if failed(i)])
          return Failure("Unable to create servers: %s" % failed_servers)

      return Success("Successfully created all servers")

          

Composing Functions
--------------------------


::


  >>> from smonad.decorators import maybe
  >>> parse_int = maybe(int)
  >>> parse_int(42)
  Just(42)
  >>> parse_int('42')
  Just(42)
  >>> parse_int('42.2')
  Nothing

  >>> parse_float = maybe(float)
  >>> parse_float('42.2')
  Just(42.2)

  >>> from smonad.actions import tryout
  >>> parse_number = tryout(parse_int, parse_float)
  >>> tokens = [2, '0', '4', 'eight', '10.0']
  >>> [parse_number(token) for token in tokens]
  [Just(2), Just(0), Just(4), Nothing, Just(10.0)]

  >>> @maybe
  ... def reciprocal(n):
  ...     return 1. / n
  >>> reciprocal(2)
  Just(0.5)
  >>> reciprocal(0)
  Nothing

  >>> process = parse_number >> reciprocal
  >>> process('4')
  Just(0.25)
  >>> process('0')
  Nothing
  >>> [process(token) for token in tokens]
  [Just(0.5), Nothing, Just(0.25), Nothing, Just(0.1)]
  >>> [parse_number(token) >> reciprocal for token in tokens]
  [Just(0.5), Nothing, Just(0.25), Nothing, Just(0.1)]
  >>> [parse_number(token) >> reciprocal >> reciprocal for token in tokens]
  [Just(2.0), Nothing, Just(4.0), Nothing, Just(10.0)]



Requirements
============

- CPython >= 2.7


Installation
============

Install from PyPI::

  pip install smonad

Install from source, download source package, decompress, then ``cd`` into source directory, run::

  make install


License
=======

BSD New, see LICENSE for details.


Links
=====

Documentation:
  http://smonad.readthedocs.org/

Issue Tracker:
  https://github.com/bryanwb/smonad/issues/

Source Package @ PyPI:
  https://pypi.python.org/pypi/smonad/

Git Repository @ Github:
  https://github.com/bryanwb/smonad/
