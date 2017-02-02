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


How?
----

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


Why?
----

Why not.


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
