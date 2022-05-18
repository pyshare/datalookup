from __future__ import annotations

from abc import ABC, abstractmethod, abstractproperty
from typing import Any

import datalookup as dq

from datalookup.utils import LOOKUP_SEP, RegisterLookupMixin


def get_field_class(name: str, value: Any) -> Field:
    """Get the ``Field`` corresponding to the value"""
    if isinstance(value, dict):
        return NodeField(name, value)
    if isinstance(
        value,
        (
            list,
            tuple,
        ),
    ):
        if all([isinstance(d, dict) for d in value]):
            return DatasetField(name, value)
        else:
            return ArrayField(name, value)

    return ValueField(name, value)


class Field(ABC, RegisterLookupMixin):
    """Base class for all field types"""

    def __init__(self, name: str, value: Any = None) -> None:
        self.protected_name__ = name
        self.set_value(value)
        self._check_field_name()

    def get_name(self) -> str:
        """
        Returns the protected name of the field. We say protected as
        no name should end with __ (double underscore)
        """
        return self.protected_name__

    def get_value(self) -> Any:
        """Return the value of the Field"""
        return getattr(self, self.protected_name__)

    def set_value(self, value: Any) -> None:
        """Set the value of the Field"""
        self.validate(value)
        value = self.serialize(self.protected_name__, value)
        setattr(self, self.get_name(), value)

    def __eq__(self, __o: object) -> bool:
        if not isinstance(__o, self.__class__):
            return False
        if self.get_name() != __o.get_name():
            return False
        return self.get_value() == __o.get_value()

    def __hash__(self) -> int:
        hash_list = self.get_hash_list()
        return hash("-".join([str(i) for i in sorted(hash_list)]))

    def get_hash_list(self) -> list[int]:
        return [hash(str(self.get_name())), hash(str(self.get_value()))]

    def _check_field_name(self) -> None:
        if self.get_name().endswith(LOOKUP_SEP):
            raise NameError("Field names must not end with an underscore.")
        if "__" in self.get_name():
            raise NameError('Field names must not contain "%s".' % LOOKUP_SEP)

    def has_node(self) -> bool:
        """Check that the field contains a node"""
        return len(getattr(self, "related_node", [])) != 0

    @abstractmethod
    def validate(self, value: Any):
        """Validate the field type"""

    @abstractmethod
    def serialize(self, name: str, value: Any):
        """Serialize the value of the field"""

    @abstractmethod
    def deserialize(self):
        """Return the value as it's original"""


# ------------------------------- Value fields ------------------------------- #


class ValueField(Field):
    def validate(self, value: Any):
        if isinstance(value, (dict, list)):
            raise TypeError(f"Expected {value!r} to be different than a dict or a list")

    def serialize(self, name: str, value: Any) -> Any:
        return value

    def deserialize(self) -> dict:
        return self.get_value()


# -------------------------------- Array field ------------------------------- #


class ArrayField(ValueField):
    """A field that store a list of object and potentialy a Node"""

    def validate(self, value: Any):
        if not isinstance(value, list):
            raise TypeError(f"Expected {value!r} to be a list")

    def serialize(self, name: str, value: list):
        """Return a Node or the current value"""
        data = []
        for element in value:
            data.append(get_field_class(name, element))
        return data

    def get_hash_list(self) -> list[int]:
        hash_list = [hash(self.get_name())]
        for elem in self.get_value():
            hash_list.append(hash(elem))
        return hash_list

    def deserialize(self):
        data = []
        for element in self.get_value():
            data.append(element.deserialize())
        return data


# ------------------------------ Related fields ------------------------------ #


class RelatedField(Field):
    """Field that potentialy contains a Node"""

    @abstractproperty
    def related_node(self):
        """Node related to the field"""

    def deserialize(self) -> dict:
        return self.get_value().values()


class NodeField(RelatedField):
    """A field that store a node"""

    @property
    def related_node(self):
        return [self.get_value()]

    def validate(self, value: dict):
        if not isinstance(value, dict):
            raise TypeError(f"Expected {value!r} to be a dict")

    def serialize(self, name: str, value: dict) -> dq.Node:
        return dq.Node(value)


class DatasetField(RelatedField):
    @property
    def related_node(self):
        return self.get_value().nodes

    def validate(self, value: Any):
        if not isinstance(value, list):
            raise TypeError(f"Expected {value!r} to be a list")
        if not all([isinstance(d, dict) for d in value]):
            raise ValueError("DatasetField value must be a list of dictionary")

    def serialize(self, name: str, value: list):
        """Return a Node or the current value"""
        return dq.Dataset(value)

    def get_hash_list(self) -> list[int]:
        hash_list = [hash(self.get_name())]
        for elem in self.get_value():
            hash_list.append(hash(elem))
        return hash_list
