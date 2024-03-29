============
Coding style
============

Please use following document when writing code for Datalookup.

Pre-commit
==========

https://pre-commit.com/ is a framework for managing and maintaining multi-language
pre-commit hooks to ensure code-style and code formatting is consistent::

  $ pip install pre-commit
  $ pre-commit install
  $ pre-commit install --hook-type commit-msg

Afterwards ``pre-commit`` will run whenever you commit. The first commit might take
some time as pre-commit will install the hooks in their own environment.
Subsequent checks will be significantly faster.

Python styles
=============

Unless it is specified in this document, follow :pep:`8`

* Use `flake8`_ to check that :pep:`8` is fully respected under the modification
  you have done.

* All files should be formatted using the `black`_ auto-formatter.

* Use `isort <https://github.com/PyCQA/isort#readme>`_ to automate import
  sorting.

To avoid installing each tool one by one, we recommend that you use ``tox``.
To install and run tox::

    $ python -m pip install tox
    $ tox -e black,flake8,isort

Space and Indentation
---------------------

* Use 4 spaces per indentation level.

* Use four spaces hanging indentation rather than vertical alignment::

    msg = (
        'Here is a multiline error message '
        'shortened for clarity.'
    )

* The closing brace/bracket/parenthesis on multiline constructs may lined
  up under the first character of the line that starts the multiline construct, as in::

    my_list = [
        1, 2, 3,
        4, 5, 6,
    ]

    result = some_function_that_takes_arguments(
        'a', 'b', 'c',
        'd', 'e', 'f',
    )

* Max line length to 88 for the code and 79 for comments.

* Avoid trailing whitespace anywhere. Try to use a linter in your IDE.

Comments
--------

* Avoid inline comment as much as possible.

* Use ``sphinx`` docstring in function.

Naming Conventions
------------------

* Use underscores, not camelCase, for variables, functions and method names::

    def my_super_function():
        my_variable = 'Datalookup'

* Class names should use the CapWords convention::

    class MySuperClass:
        pass

* Use UPPER_CASE_WITH_UNDERSCORES for constant variable.

Imports
-------

* Break long lines using parentheses and indent continuation lines by 4 spaces.

  Use a single blank line between the last import and any module level code,
  and use two blank lines above the first function or class.

* Put imports in the following orders: future, standard library, third-party libraries,
  other Datalookup components, local Datalookup component, try/excepts

* Sort lines in each group alphabetically by the full module name.

.. _flake8: https://pypi.org/project/flake8/
.. _black: https://black.readthedocs.io/en/stable/
