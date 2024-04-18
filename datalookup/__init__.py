from __future__ import annotations

import functools
import importlib
import json

from collections import OrderedDict, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any, Iterator, Tuple, Type, Union

from datalookup.exceptions import FieldNotFound, FilterDoesNotExist, ObjectNotFound
from datalookup.fields import DatasetField, Field, get_field_class
from datalookup.utils import LOOKUP_SEP, REPR_OUTPUT_SIZE, hash_list

if TYPE_CHECKING:  # pragma: no cover
    from datalookup.lookup import Lookup

__all__ = ["Dataset", "Node", "__version__", "version_tuple"]

try:
    from ._version import version as __version__
    from ._version import version_tuple
except ImportError:  # pragma: no cover
    # broken installation, we don't even try
    # unknown only works because we do poor mans version compare
    __version__ = "unknown"
    version_tuple = (0, 0, "unknown")  # type:ignore[assignment]


@dataclass
class Filter:
    """Store information to retrieve nodes when filtering"""

    value: str
    field_name: str
    lookup_name: str


class Dataset:
    """Base class that store a set of nodes that can be manipulated and filtered"""

    def __init__(self, data: Union[dict, list]) -> None:
        self.nodes: list[Node] = []
        self._populate(data)

    def __repr__(self):
        data = list(self[: REPR_OUTPUT_SIZE + 1])
        if len(data) > REPR_OUTPUT_SIZE:
            data[-1] = "...(remaining elements truncated)..."
        return "<{} {}>".format(self.__class__.__name__, repr(data))

    def __eq__(self, __o: object) -> bool:
        if not isinstance(__o, Dataset):
            return False
        if set(self.nodes) != set(__o.nodes):
            return False
        return True

    def __hash__(self) -> int:
        return hash_list(self.nodes)

    def __len__(self):
        return len(self.nodes)

    def __iter__(self) -> Iterator[Node]:
        for node in self.nodes:
            yield node

    def __getitem__(self, indices: Union[int, slice]) -> Union[Node, list[Node]]:
        """Retrieve an item or slice from the set of results."""
        if not isinstance(indices, (int, slice)):
            raise TypeError(
                "Dataset indices must be integers or slices, not {}.".format(
                    type(indices).__name__
                )
            )
        if (isinstance(indices, int) and indices < 0) or (
            isinstance(indices, slice)
            and (
                (indices.start is not None and indices.start < 0)
                or (indices.stop is not None and indices.stop < 0)
            )
        ):
            raise ValueError("Negative indexing is not supported.")

        return list(self)[indices]

    def __or__(self, other: Dataset):
        """Combine two or more dataset"""
        dataset = self.distinct()
        for node in other.nodes:
            if node in dataset:
                continue
            dataset.nodes.append(node)
        return dataset

    @classmethod
    def from_json(cls, file: Union[str, Path]):
        """Create a Dataset based on a json file"""
        with open(str(file), "r") as fp:
            content = json.load(fp)
        return cls(content)

    @classmethod
    def from_nodes(cls, nodes: list[Node]):
        """Create a Dataset based on a list of Node"""
        if not isinstance(nodes, list):
            raise TypeError("'nodes' must be a list")
        if not all([isinstance(n, Node) for n in nodes]):
            raise TypeError("'nodes' must be a list of Node")
        dataset = cls([])
        dataset.nodes = nodes
        return dataset

    def _populate(self, data: Union[dict, list]) -> None:
        """Populate the dataset with Nodes"""
        if isinstance(data, dict):
            self.nodes.append(Node(data))
        elif isinstance(data, list):
            if not all([isinstance(d, dict) for d in data]):
                raise ValueError(
                    "Cannot create a Dataset based on a list where all the "
                    "element are not a dictionary"
                )
            else:
                self.nodes = [Node(d) for d in data]
        else:
            raise ValueError("'data' must be of type 'dict' or 'list'")

    def values(self) -> list:
        """Returns a list of dictionaries instead of a Dataset."""
        values = []
        for node in self:
            values.append(node.values())
        return values

    @staticmethod
    def _filter(nodes: list[Node], **kwargs: Any) -> Dataset:
        data: list[Node] = []
        for node in nodes:
            try:
                filtered_node = node.filter(**kwargs)
            except ObjectNotFound:
                continue
            else:
                data.append(filtered_node)

        # Update the current dataset
        return Dataset.from_nodes(data)

    def filter(self, **kwargs) -> Dataset:
        """
        Returns a new Dataset containing objects that match the given filter parameters.

        The filter parameters (``**kwargs``) should be in the following format
        ``field__lookuptype=value``. Example::

            data = [
                {
                    "author": "J. K. Rowling",
                    "books": {
                        "genre": "Fantasy"
                    }
                }
            ]

            books = Dataset(data)
            books.filter(author__exact="J. K. Rowling")
            books.filter(books__genre__in=["Fantasy"])
        """
        return self._filter(self.nodes, **kwargs)

    def _search_related_node(self, name: str, nodes: list[Node]) -> list[Node]:
        """
        Search in the dataset a related node with the given name. This method
        is recursive and will search in every dataset. Return a a list of Nodes
        """
        related_node: list[Node] = []
        fields_name = name.split(".")
        for node in nodes:
            field = node.get_field(fields_name[0])
            field_nodes = getattr(field, "related_node", [])
            if len(fields_name) == 1:
                related_node.extend(field_nodes)
            else:
                related_node.extend(
                    self._search_related_node(".".join(fields_name[1:]), field_nodes)
                )
        return related_node

    def filter_related(self, name: str, **kwargs) -> Dataset:
        """
        Same as :meth:`filter` but for related field. The name of the field to filter
        must be specified. Returns a Dataset of the specified related field.

        :param name: Name of the related field
        :return: New Dataset
        """
        nodes = self._search_related_node(name, self.nodes)
        return self._filter(nodes, **kwargs)

    def exclude(self, **kwargs) -> Dataset:
        """
        Returns a new Dataset containing objects that do not match the given filter
        parameters.

        The filter parameters (``**kwargs``) should be in the following format
        ``field__lookuptype=value``. Example::

            data = [
                {
                    "author": "J. K. Rowling",
                    "books": {
                        "genre": "Fantasy"
                    }
                }
            ]

            books = Dataset(data)
            books.exclude(author__exact="J. K. Rowling")
            books.exclude(books__genre__in=["Fantasy"])
        """
        if not kwargs:
            return self

        data: list[Node] = []
        for node in self:
            try:
                node.filter(**kwargs)
            except ObjectNotFound:
                data.append(node)
        return Dataset.from_nodes(data)

    def distinct(self) -> Dataset:
        """Returns a new Dataset without duplicate entry."""
        distinct_nodes = []
        for node in self.nodes:
            if node in distinct_nodes:
                continue
            distinct_nodes.append(node)
        return Dataset.from_nodes(distinct_nodes)

    def on_cascade(self) -> Dataset:
        """
        Must be followed by :meth:`filter()`, :meth:`exclude()` or other filtering
        methods (like books.on_cascade().filter(...)). This method will not only
        filter the current dataset but also the related field dataset. Example::

            # Filter the author but also the books of the author
            authors = books.on_cascade().filter(
                books__name="Harry Potter and the Chamber of Secrets"
            )
        """
        for node in self.nodes:
            node.activate_on_cascade()
        return self


class Node:
    """
    Base class that represent a dictionary where the value of a
    key is a specific Field
    """

    def __init__(self, data: dict) -> None:
        self.fields: OrderedDict[str, Field] = OrderedDict()
        self.on_cascade = False
        self._populate(data)

    def __eq__(self, __o: object) -> bool:
        if not isinstance(__o, Node):
            return False
        if set(self.fields.values()) != set(__o.fields.values()):
            return False
        return True

    def __hash__(self) -> int:
        hash_list = []
        for element in self.fields.values():
            hash_list.append(hash(element))
        return hash("-".join([str(i) for i in sorted(hash_list)]))

    def __getattr__(self, name: str) -> Any:
        try:
            return self.get_field(name).get_value()
        except FieldNotFound:
            raise AttributeError(f"{name} attribute does not exist")

    def __repr__(self):
        return "<{}: {}>".format(self.__class__.__name__, self)

    def __str__(self):
        return "{} object ({})".format(
            self.__class__.__name__, list(self.fields.values())[0].get_value()
        )

    def activate_on_cascade(self):
        """Activate filtering on cascade"""
        self.on_cascade = True
        for field in self.fields.values():
            for node in getattr(field, "related_node", []):
                node.activate_on_cascade()

    def _populate(self, data: dict) -> None:
        """Populate the node with the given data"""
        if not isinstance(data, dict):
            raise ValueError("'data' must be of type dict")
        for key, value in data.items():
            self.fields[key] = get_field_class(key, value)

    def get_field(self, name: str) -> Field:
        """Return a field of the current node"""
        for field in self.fields.values():
            if field.get_name() == name:
                return field
        raise FieldNotFound("{} field not found in {}".format(name, self.values()))

    def get_lookup(self, field: Field, lookup_name: str) -> Type[Lookup]:
        """Return the lookup class of a field"""
        lookup = field.get_lookup(lookup_name)
        if not lookup:
            raise LookupError(
                "'{}' lookup not found in: {}".format(lookup_name, field.class_lookups)
            )
        return lookup

    @staticmethod
    def get_node_filters(node: Node, parent: str) -> set[str]:
        """Return a set of filters for the current node"""
        filters = set()
        for child_filter in node.get_filters():
            filters.add(f"{parent}{LOOKUP_SEP}{child_filter}")
        return filters

    @functools.lru_cache(maxsize=None)
    def get_filters(self) -> set[str]:
        filters = set()
        for key, field in self.fields.items():
            filters.add(key)
            for node in getattr(field, "related_node", []):
                filters = filters.union(self.get_node_filters(node, key))
        return filters

    def get_match_filter(self, param: str) -> str:
        """Return a filter if the value starts with an existing filter"""
        partition = {}
        for filter in self.get_filters():
            rpart = param.rpartition(filter)
            if not rpart[1] or rpart[0]:
                continue
            partition.update({rpart[1]: len(rpart[1].split(LOOKUP_SEP))})

        return max(partition, key=lambda k: partition[k])

    def get_lookup_name(self, param: str, filter: str) -> str:
        """Return the lookup based on a param and it's filter"""
        _, _, lookup_name = param.rpartition(filter)
        if not lookup_name:
            lookup_name = "exact"
        else:
            lookup_name = lookup_name.strip(LOOKUP_SEP)
        return lookup_name

    def _parser_filters(self, **kwargs: Any) -> Tuple[list[Filter], dict]:
        """
        Return a list of Filter that are use to filter the current
        instance and a dictionary of filters for it's childs.
        """
        current_filters = []
        next_filters: defaultdict[str, dict] = defaultdict(dict)

        for param, value in kwargs.items():
            filter = self.get_match_filter(param)
            splitted_filter = filter.split(LOOKUP_SEP)
            if len(splitted_filter) == 1:
                lookup_name = self.get_lookup_name(param, filter)
                current_filters.append(Filter(value, splitted_filter[0], lookup_name))
            else:
                # Remove the parent node from the kwargs attribute. This is for
                # related next filtering
                parent_node = splitted_filter[0]
                new_param = param.replace(parent_node + LOOKUP_SEP, "", 1)
                next_filters[parent_node].update({new_param: value})

        return current_filters, next_filters

    def filter(self, **kwargs: Any) -> Node:
        """
        Returns the current :class:`Node` or raise an ``ObjectNotFound`` exception.

        The filter parameters (``**kwargs``) should be in the following format
        ``field__lookuptype=value``. Example::

            data = {
                "author": "J. K. Rowling",
                "books": {
                    "genre": "Fantasy"
                }
            }

            node = Node(data)
            node.filter(author__exact="J. K. Rowling")
            node.filter(books__genre__in=["Fantasy"])
        """
        # If there is no filter given. There is no need to proceed.
        # We can just return the actual node
        if not kwargs:
            return self

        filters = self.get_filters()
        for key in kwargs.keys():
            if not any(key.startswith(f) for f in filters):
                raise FilterDoesNotExist("{} filter does not exist".format(key))

        # Get attribute filter. This is to filter current instance
        current_filters, next_filters = self._parser_filters(**kwargs)

        # Check if one of the field of this node correspond to the current filter
        for filter in current_filters:
            field = self.get_field(filter.field_name)
            lookup_class = self.get_lookup(field, filter.lookup_name)
            lookup = lookup_class(field.get_value(), filter.value)
            if not lookup.resolve():
                raise ObjectNotFound()

        for parent, new_params in next_filters.items():
            field = self.get_field(parent)
            node_or_dataset = field.get_value()
            data = node_or_dataset.filter(**new_params)
            if isinstance(field, DatasetField):
                if len(data) == 0:
                    raise ObjectNotFound()
                if self.on_cascade is True:
                    setattr(field, field.get_name(), data)

        return self

    def values(self) -> dict:
        """
        Return a dictionary, with the keys corresponding to the attribute
        names of the node object.
        """
        data = {}
        for key, field in self.fields.items():
            data[key] = field.deserialize()
        return data


# Import lookup here to avoid import recursion and load all fields lookup
importlib.import_module("datalookup.lookup")
