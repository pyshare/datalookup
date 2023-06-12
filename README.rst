=======================================
Datalookup - Deep nested data filtering
=======================================

.. image:: https://img.shields.io/badge/python-3.9-blue.svg
    :target: https://github.com/pyshare/datalookup

.. image:: https://github.com/pyshare/datalookup/actions/workflows/tests.yml/badge.svg
    :target: https://github.com/pyshare/datalookup/actions?query=workflow%3APython%20testing

.. image:: https://codecov.io/gh/pyshare/datalookup/branch/master/graph/badge.svg
    :target: https://codecov.io/gh/pyshare/datalookup
    :alt: Code coverage Status

.. image:: https://github.com/pyshare/datalookup/actions/workflows/linters.yml/badge.svg
    :target: https://github.com/pyshare/datalookup/actions?query=workflow%3APython%20linting

.. image:: https://readthedocs.org/projects/datalookup/badge/?version=latest
    :target: https://datalookup.readthedocs.io/en/latest/
    :alt: Documentation Status

.. image:: https://img.shields.io/badge/code%20style-black-000000.svg
    :target: https://github.com/psf/black

----

The **Datalookup** library makes it easier to filter and manipulate your data. The
module is inspired by the Django Queryset Api and it's lookups.

Installation
============

.. code-block:: console

    $ pip install datalookup

Example
=======

Throughout the below examples, we'll refer to the following data,
which comprise a list of authors with the books they wrote.

.. code-block:: python

    data = [
        {
            "id": 1,
            "author": "J. K. Rowling",
            "books": [
                {
                    "name": "Harry Potter and the Chamber of Secrets",
                    "genre": "Fantasy",
                    "published": "1998"
                },
                {
                    "name": "Harry Potter and the Prisoner of Azkaban",
                    "genre": "Fantasy",
                    "published": "1999"
                }
            ]
        },
        {
            "id": 2,
            "author": "Agatha Christie",
            "books": [
                {
                    "name": "And Then There Were None",
                    "genre": "Mystery",
                    "published": "1939"
                }
            ]
        }
    ]

**Datalookup** makes it easy to find an author by calling one of the methods
of the ``Dataset`` class like ``filter()`` or ``exclude()``. There
are multiple ways to retrieve an author.

Basic filtering
---------------

Use one of the ``field`` of your author dictionary to filter your data.

.. code-block:: python

    from datalookup import Dataset

    # Use Dataset to manipulate and filter your data
    books = Dataset(data)

    # Retrieve an author using the author name
    authors = books.filter(author="J. K. Rowling")
    assert len(authors) == 1
    assert authors[0].author == "J. K. Rowling"

    # Retrieve an author using '__in' lookup
    authors = books.filter(id__in=[2, 3])
    assert len(authors) == 1
    assert authors[0].author == "Agatha Christie"

    # Retrieve an author using 'exclude' and '__contains' lookup
    authors = books.exclude(author__contains="Christie")
    assert len(authors) == 1
    assert authors[0].author == "J. K. Rowling"

Related field filtering
-----------------------

Use a related field like ``books`` separated by a ``__`` (double-underscore)
and a field of the books. Something like ``books__name``.

.. code-block:: python

    # Retrieve an author using the date when the book was published
    authors = books.filter(books__published="1939")
    assert len(authors) == 1
    assert authors[0].author == "Agatha Christie"

    # Retrieve an author using '__regex' lookup
    authors = books.filter(books__name__regex=".*Potter.*")
    assert len(authors) == 1
    assert authors[0].author == "J. K. Rowling"

AND, OR - filtering
-------------------

Keyword argument queries - in filter(), etc. - are "AND"ed together.
If you need to execute more complex queries (for example, queries with OR statements),
you can combine two filter request with "|".

.. code-block:: python

    # Retrieve an author using multiple filters with a single request (AND). This
    # filter use the '__icontains' lookup. Same as '__contains' but case-insensitive
    authors = books.filter(books__name__icontains="and", books__genre="Fantasy")
    assert len(authors) == 1
    assert authors[0].author == "J. K. Rowling"

    # Retrieve an author by combining filters (OR)
    authors = books.filter(author="Stephane Capponi") | books.filter(
        author="J. K. Rowling"
    )
    assert len(authors) == 1
    assert authors[0].author == "J. K. Rowling"

Filter nested related field
----------------------------

The library provides also a way to filter nested relationship. This means that you
can make requests to only retrieve ``books`` in the author collection. Or you can
use that output to filter the authors.

.. code-block:: python

    # filter_related is the method to use to filter all related nodes
    related_books = books.filter_related('books', genre="Mystery")
    assert len(related_books) == 1
    assert related_books[0].name == "And Then There Were None"

    # You can also use filter_related to filter authors.
    authors = books.filter(
        books=books.filter_related('books', name__regex=".*Potter.*")
    )
    assert len(authors) == 1
    assert authors[0].author == "J. K. Rowling"

Cascade filtering
-----------------

Sometimes you will want to filter the author but also the related books.
It is possible to do that by calling the ``on_cascade()`` method before filtering.

.. code-block:: python

    # Filter the author but also the books of the author
    authors = books.on_cascade().filter(
        books__name="Harry Potter and the Chamber of Secrets"
    )
    assert len(authors) == 1
    assert authors[0].author == "J. K. Rowling"

    # The books are also filtered
    assert len(authors[0].books) == 1
    assert authors[0].books[0].name == "Harry Potter and the Chamber of Secrets"

List of available lookups
=========================

Field lookups are used to specify how a the dataset should query the results it returns.
They're specified as keyword arguments to the ``Dataset`` methods
``filter()`` and ``exclude()``. Basic lookups keyword arguments
take the form "field__lookuptype=value". (That's a double-underscore).

As a convenience when no lookup type is provided (like in
``books.filter(id=1)``) the lookup type is assumed to be ``exact``.

.. code-block:: python

    # author is one of the field of the dictionary
    # '__contains' is the lookup
    books.filter(author__contains="Row")

+--------------+-------------------------+-----------------------------------------------------------------+
| Lookup       | Case-insensitive lookup | Description                                                     |
+==============+=========================+=================================================================+
| exact        | iexact                  | Exact match                                                     |
+--------------+-------------------------+-----------------------------------------------------------------+
| contains     | icontains               | Containment test                                                |
+--------------+-------------------------+-----------------------------------------------------------------+
| startswtih   | istartswith             | Starts with a specific string                                   |
+--------------+-------------------------+-----------------------------------------------------------------+
| endswith     | iendswith               | Ends with a specific string                                     |
+--------------+-------------------------+-----------------------------------------------------------------+
| regex        | iregex                  | Regular expression match                                        |
+--------------+-------------------------+-----------------------------------------------------------------+
| in           |                         | In a given iterable; strings (being iterables) are accepted     |
+--------------+-------------------------+-----------------------------------------------------------------+
| gt           |                         | Grater than                                                     |
+--------------+-------------------------+-----------------------------------------------------------------+
| gte          |                         | Greater that or equal                                           |
+--------------+-------------------------+-----------------------------------------------------------------+
| lt           |                         | Lower than                                                      |
+--------------+-------------------------+-----------------------------------------------------------------+
| lte          |                         | Lower than or equal to                                          |
+--------------+-------------------------+-----------------------------------------------------------------+
| range        |                         | Range between two values. Integer only                          |
+--------------+-------------------------+-----------------------------------------------------------------+
| isnull       |                         | Check that a field is null. Takes either True or False          |
+--------------+-------------------------+-----------------------------------------------------------------+
| contained_by |                         | Check data is a subset of the passed values. ArrayField only    |
+--------------+-------------------------+-----------------------------------------------------------------+
| overlap      |                         | Data shares any results with the passed values. ArrayField only |
+--------------+-------------------------+-----------------------------------------------------------------+
| len          |                         | Check length of the array. ArrayField only                      |
+--------------+-------------------------+-----------------------------------------------------------------+

Documentation
=============

Datalookup does not stop here. The full documentation is in the ``docs``
directory or online at https://datalookup.readthedocs.io/en/latest/

Contribution
============

Anyone can contribute to Datalookup's development. Checkout our documentation on how to
get involved: `https://datalookup.readthedocs.io/en/latest/internals/contributing.html`

License
=======

Copyright Stephane Capponi and others, 2023
Distributed under the terms of the `MIT`_ license, Datalookup is free and
open source software.

Datalookup was inspired by Django and only the `RegisterLookupMixin`_ was
copied. Everything else was inspired and re-interpreted.
You can find the license of Django in the ``licenses`` folder.

.. _`MIT`: https://github.com/pyshare/datalookup/blob/master/LICENCE
.. _`RegisterLookupMixin`: https://github.com/pyshare/datalookup/blob/78d315e474d842d82a392127e835cb304940d1c7/datalookup/utils.py#LL20C10-L20C10
