========================
Datalookup documentation
========================

.. currentmodule:: datalookup

The **Datalookup** library makes it easier to filter and manipulate your data. The
module is inspired by the Django Queryset Api and it's lookups.

.. note::

    This documentation will copy some information of the Django documentation.
    All ``lookups`` have the same name as in Django and some method's name from the Queryset
    are also the same. However it's important to note that **Datalookup** is not Django.
    It's just a simple module for deep nested data filtering.

Installation
============

.. code-block:: console

    $ pip install datalookup

Example
=======

Throughout the below examples (and in the reference), we'll refer to the following data,
which comprise a list of authors with the books they wrote.

.. code-block:: Python

    data = [
        {
            "id": 1,
            "author": "J. K. Rowling",
            "books": [
                {
                    "name": "Harry Potter and the Chamber of Secrets",
                    "genre": "Fantasy",
                    "published": "1998",
                    "sales": 77000000,
                    "info": {
                        "pages": 251,
                        "language": "English"
                    }
                },
                {
                    "name": "Harry Potter and the Prisoner of Azkaban",
                    "genre": "Fantasy",
                    "published": "1999",
                    "sales": 65000000,
                    "info": {
                        "pages": 317,
                        "language": "English"
                    }
                }
            ],
            "genres": [
                "Fantasy",
                "Drama",
                "Crime fiction"
            ]
        },
        {
            "id": 2,
            "author": "Agatha Christie",
            "books": [
                {
                    "name": "And Then There Were None",
                    "genre": "Mystery",
                    "published": "1939",
                    "sales": 100000000,
                    "info": {
                        "pages": 272,
                        "language": "English"
                    }
                }
            ],
            "genres": [
                "Murder mystery",
                "Detective story",
                "Crime fiction",
                "Thriller"
            ]
        }
    ]

**Datalookup** makes it easy to find an author by calling one of the methods
of the :class:`Dataset` class like :meth:`filter()` or :meth:`exclude()`. There
are multiple ways to retrieve an author.

Basic filtering
---------------

Use one of the ``field`` of your author dictionary to filter your data.

.. note::

    Datalookup consider a dictionary as a :class:`Node`. Each ``keys`` of the
    dictionary is converted to a ``Field``. Each dictionary can contain one or multiple
    fields. Some fields are considered ``ValueField`` and others ``RelatedField``.
    Those fields are what will help us filter your dataset.

.. code-block:: python

    from datalookup import Dataset

    # Use Dataset to manipulate and filter your data. We assume for the
    # next examples that this line will be added.
    books = Dataset(data)
    assert len(books) == 2

    # Retrieve an author using one of the field of the author.
    # Something like 'id' or 'author'
    authors = books.filter(author="J. K. Rowling")
    assert len(authors) == 1
    assert authors[0].author == "J. K. Rowling"

Related field filtering
-----------------------

Use a related field like ``books`` separated by a ``__`` (double-underscore)
and a field of the books. Something like ``books__name``.

.. code-block:: python

    # We can retrive all authors that published a book in 1939 using the 'published'
    # books field
    authors = books.filter(books__published="1939")
    assert len(authors) == 1
    assert authors[0].author == "Agatha Christie"

AND, OR - filtering
-------------------

Keyword argument queries - in :meth:`filter()`, etc. - are "AND"ed together.
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
It is possible to do that by calling the :meth:`on_cascade()` method before filtering.

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

Lookup filtering
----------------

You might have seen in the previous examples the use of ``lookups`` to retrieve
authors or books. Here are a couple more examples:

.. code-block:: python

    # Use of the '__contains' lookup to look into the 'genres' fields
    authors = books.filter(genres__contains="Fantasy")

    # Use of the '__gt' lookup to get all authors that wrote a book with
    # more than 'X' pages
    authors = books.filter(books__info__pages__gt=280)

    # Same as above but with '__range'. Find author that wrote a book
    # with the numbers of pages between 'X' and 'y'
    authors = books.filter(books__info__pages__range=(250, 350))

**Dataset** Api
===============

Here's the formal declaration of a **Dataset**:

.. class:: Dataset(data: Union[dict, list])

    A **Dataset** is the entry point to manipulate and filter your data. Usually
    when you'll interact with a **Dataset** you'll use it by chaining filters.
    To make this work, most methods return new dataset. These methods are
    covered in detail later in this section.

    .. note::

        A **Dataset** will accept a dictionary for the data parameter. Bear in mind
        that if you use ``values`` on this kind of dataset, it will still return
        a list of dictionary.

Class methods
-------------

``from_json()``
~~~~~~~~~~~~~~~

.. method:: Dataset.from_json(file: str)

    Return a :class:`Dataset` from a json file.

----

``from_nodes()``
~~~~~~~~~~~~~~~~

.. method:: Dataset.from_nodes(nodes: list[Node])

    Return a :class:`Dataset` from a list of Nodes. This is mostly
    use internally.


Methods that return new **Dataset**
-----------------------------------

``filter()``
~~~~~~~~~~~~

.. method:: Dataset.filter(**kwargs)

    Returns a new Dataset containing objects that match the given filter parameters.

    The filter parameters (``**kwargs``) should be in the format described in the
    `Field lookups`_ below. Multiple parameters will be ``AND``\sed together

----

``filter_related()``
~~~~~~~~~~~~~~~~~~~~

.. method:: Dataset.filter_related(field: str, **kwargs)

    Same as :meth:`filter` but for related field. The name of the field to filter
    must be specified. Returns a **Dataset** of the specified related field.

----

``exclude()``
~~~~~~~~~~~~~

.. method:: Dataset.exclude(**kwargs)

    Returns a new Dataset containing objects that do not match the given filter
    parameters.

    The filter parameters (``**kwargs``) should be in the format described in the
    `Field lookups`_ below. Multiple parameters will be ``AND``\sed together

----

``distinct()``
~~~~~~~~~~~~~~

.. method:: Dataset.distinct()

    Returns a new Dataset without duplicate entry.

----

``values()``
~~~~~~~~~~~~

.. method:: Dataset.values()

    Returns a list of dictionaries instead of a Dataset.

----

``on_cascade()``
~~~~~~~~~~~~~~~~

.. method:: Dataset.on_cascade()

    Must be followed by :meth:`filter()`, :meth:`exclude()` or other filtering
    methods (like books.on_cascade().filter(...)). This method will not only
    filter the current dataset but also the related field dataset. Example:

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

.. _field-lookups:

**Field** lookups
-----------------

Field lookups are used to specify how a the dataset should query the results it returns.
They're specified as keyword arguments to the ``Dataset`` methods
:meth:`~datalookup.Dataset.filter()` and :meth:`~datalookup.Dataset.exclude()`.
Basic lookups keyword arguments take the form "field__lookuptype=value".
(That's a double-underscore).

As a convenience when no lookup type is provided (like in
``books.filter(id=1)``) the lookup type is assumed to be :lookup:`exact`.

.. fieldlookup:: exact

``exact``
~~~~~~~~~

Exact match.

Examples::

    books.filter(id__exact=1)

----

.. fieldlookup:: iexact

``iexact``
~~~~~~~~~~

Case-insensitive exact match.

Example::

    books.filter(author__iexact='j. k. rowling')

----

.. fieldlookup:: contains

``contains``
~~~~~~~~~~~~

Case-sensitive containment test. Value type can be a 'list'

Example::

    books.filter(books__name__contains='And')
    books.filter(books__name__contains=['And', 'Potter'])

----

.. fieldlookup:: icontains

``icontains``
~~~~~~~~~~~~~

Case-insensitive containment test. Value type can be a 'list'

Example::

    books.filter(books__name__contains='and')
    books.filter(books__name__contains=['and', 'potter'])

----

.. fieldlookup:: in

``in``
~~~~~~

In a given iterable; often a list, tuple, or dataset. It's not a common use
case, but strings (being iterables) are accepted.

Examples::

    books.filter(id__in=[1, 3, 4])
    books.filter(author__in='abc')

----

.. fieldlookup:: gt

``gt``
~~~~~~

Greater than.

Example::

    books.filter(id__gt=1)

----

.. fieldlookup:: gte

``gte``
~~~~~~~

Greater than or equal to.

----

.. fieldlookup:: lt

``lt``
~~~~~~

Less than.

----

.. fieldlookup:: lte

``lte``
~~~~~~~

Less than or equal to.

----

.. fieldlookup:: startswith

``startswith``
~~~~~~~~~~~~~~

Case-sensitive starts-with.

Example::

    books.filter(author__startswith='J.')

----

.. fieldlookup:: istartswith

``istartswith``
~~~~~~~~~~~~~~~

Case-insensitive starts-with.

Example::

    books.filter(author__istartswith='j.')

----

.. fieldlookup:: endswith

``endswith``
~~~~~~~~~~~~

Case-sensitive ends-with.

Example::

    books.filter(books__name__endswith='Azkaban')

----

.. fieldlookup:: iendswith

``iendswith``
~~~~~~~~~~~~~

Case-insensitive ends-with.

Example::

    books.filter(books__name__endswith='azkaban')

----

.. fieldlookup:: range

``range``
~~~~~~~~~

Range test (inclusive).

Example::

    books.filter(books__info__pages__range=(250, 350))

----

.. fieldlookup:: isnull

``isnull``
~~~~~~~~~~

Takes either ``True`` or ``False``, which correspond to None in Python.

Example::

    books.filter(books__sales__isnull=True)

----

.. fieldlookup:: regex

``regex``
~~~~~~~~~

Case-sensitive regular expression match. This feature is provided by a
(Python) user-defined REGEXP function, and the regular expression syntax
is therefore that of Python's ``re`` module.

Example::

    books.filter(author__regex=r'.*Row.*')

----

.. fieldlookup:: iregex

``iregex``
~~~~~~~~~~

Case-insensitive regular expression match.

Example::

    books.filter(author__regex=r'.*row.*')

**ArrayField**\s lookups
------------------------

There are special lookups for ArrayField like::

    "genres": [
        "Fantasy",
        "drama",
        "crime fiction"
    ]

----

.. fieldlookup:: arrayfield.contained_by

``contained_by``
~~~~~~~~~~~~~~~~

This is the opposite of the :lookup:`contains` lookup - the objects returned
will be those where the data is a subset of the values passed. For example:

.. code-block:: python

    authors = books.filter(
        genres__contained_by=["Fantasy", "Drama", "Crime fiction"]
    )
    assert len(authors) == 1

----

.. fieldlookup:: arrayfield.overlap

``overlap``
~~~~~~~~~~~

Returns objects where the data shares any results with the values passed.

.. code-block:: python

    authors = books.filter(genres__overlap=["Fantasy"])
    assert len(authors) == 1

    authors = books.filter(genres__overlap=["Fantasy", "Thriller"])
    assert len(authors) == 2

----

.. fieldlookup:: arrayfield.len

``len``
~~~~~~~

Returns the length of the array. For example:

.. code-block:: python

    authors = books.filter(genres__len=3)
    assert len(authors) == 1
    assert authors[0].name == "J. K. Rowling"

.. fieldlookup:: arrayfield.index

**Node** class
==============

Here's the formal declaration of a **Node**:

.. class:: Node(data: dict)

    A **Node** represent a dictionary where the value of each key is a specific Field.
    Right now exists two categories of Fields. ``ValueField`` and ``RelatedField``.
    The first one is used for - int, float, str. And the second one for
    dictionary and list of dictionary.

    Thanks to those fields we are able to filter and find every nodes
    that the user query.

Methods
-------

``filter()``
~~~~~~~~~~~~

.. method:: Node.filter(**kwargs)

    Returns the current :class:`Node` or raise an ``ObjectNotFound`` exception.

    The filter parameters (``**kwargs``) should be in the format described in the
    `Field lookups`_ below. Multiple parameters will be ``AND``\sed together

----

``values()``
~~~~~~~~~~~~

.. method:: Node.values()

    Returns a dictionary, with the keys corresponding to the field
    names of the node object.
