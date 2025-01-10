.. _installation:

============
Installation
============

Installation Users
==================

SymBRiM is currently available on PyPI. ::

    pip install symbrim

The optional dependencies can be installed with: ::

    pip install bicycleparameters
    pip install symmeplot

Installation Developers
=======================

SymBRiM uses `poetry`_ as package manager. To install SymBRiM after installing `poetry`_
and cloning the repository, run: ::

    poetry install

SymBRiM offers dependency groups to assist developers:

- ``lint``: packages required for linting.
- ``test``: packages required for testing.
- ``docs``: packages required for building the documentation.

To install optional dependencies from a specific group, run: ::

    poetry install --with <group>

Some of the additional utilities also require extra packages. These can be installed
using: ::

    poetry install --extras parametrize
    poetry install --extras plotting

To install everything at once, run: ::

    poetry install --with lint,test,docs --all-extras

To quickly check code for linting errors, it is recommended to set up ``pre-commit``
hooks by executing: ::

    pre-commit install

.. _poetry: https://python-poetry.org
