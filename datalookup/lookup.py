import re

from abc import ABC, abstractmethod
from collections.abc import Iterable
from typing import Any, Optional

from datalookup import Dataset
from datalookup.fields import ArrayField, DatasetField, Field


class LookupRegistryError(Exception):
    """Exception raised on lookup class registration"""


class Lookup(ABC):
    """Base class for filter lookup"""

    lookup_name: Optional[str] = None
    filter_types: Optional[Any] = None

    def __init__(self, field_value, filter_value) -> None:
        self.filter_value = self.prepare_filter_value(filter_value)
        self.field_value = self.prepare_field_value(field_value)

    def prepare_filter_value(self, filter_value: Any) -> Any:
        """
        Prepare the filter value. Modify it before matching with
        the node value
        """
        return filter_value

    def prepare_field_value(self, field_value: Any) -> Any:
        """
        Prepare the field value. Modify it before matching with
        the filter value
        """
        return field_value

    def resolve(self):
        """
        Check that the filter value or the node value are correct and
        verify that the filter is matching the field value
        """
        self.check_filter_value_type(self.filter_value)
        return self.is_matching(self.field_value, self.filter_value)

    def check_filter_value_type(self, filter_value: Any):
        """Check that the filter value has the correct type"""
        if self.filter_types is None:
            return
        if not isinstance(filter_value, self.filter_types):
            raise TypeError(
                'Cannot apply lookup "{}" on "{}" node attr as it '
                'is of type "{}"'.format(
                    self.lookup_name, self.field_value, type(filter_value)
                )
            )

    @abstractmethod
    def is_matching(self, field_value: Any, filter_value: Any):
        """Check that the filter value match a value in the node"""


class CaseInsensitive(Lookup):
    def prepare_filter_value(self, filter_value: str) -> str:
        return filter_value.lower()

    def prepare_field_value(self, field_value: str) -> str:
        return field_value.lower()


# -------------------------------- Base lookup ------------------------------- #


@Field.register_lookup
class Exact(Lookup):
    lookup_name = "exact"

    def is_matching(self, field_value: Any, filter_value: Any):
        return field_value == filter_value


@Field.register_lookup
class IExact(CaseInsensitive, Exact):
    lookup_name = "iexact"


@Field.register_lookup
class Regex(Lookup):
    lookup_name = "regex"
    filter_types = (str,)

    def is_matching(self, field_value: Any, filter_value: str):
        if re.match(filter_value, field_value):
            return True
        return False


@Field.register_lookup
class IRegex(CaseInsensitive, Regex):
    lookup_name = "iregex"

    def prepare_filter_value(self, filter_value: str) -> str:
        # Do not modify regex filtering value
        return filter_value


@Field.register_lookup
class In(Lookup):
    lookup_name = "in"
    filter_types: Any = (Iterable,)

    def is_matching(self, field_value: Any, filter_value: Iterable):
        return field_value in filter_value


@Field.register_lookup
class Range(Lookup):
    lookup_name = "range"

    def is_matching(self, field_value: Any, filter_value: tuple):
        return field_value in range(filter_value[0], filter_value[1])


@Field.register_lookup
class IsNull(Lookup):
    lookup_name = "isnull"
    filter_types = (bool,)

    def is_matching(self, field_value: None, filter_value: bool):
        if filter_value is True:
            if field_value is None:
                return True
        else:
            if field_value is not None:
                return True
        return False


# ----------------------------- Comparison lookup ---------------------------- #


@Field.register_lookup
class GreaterThan(Lookup):
    lookup_name = "gt"

    def is_matching(self, field_value: Any, filter_value: Any):
        return field_value > filter_value


@Field.register_lookup
class GreaterThanOrEqual(Lookup):
    lookup_name = "gte"

    def is_matching(self, field_value: Any, filter_value: Any):
        return field_value >= filter_value


@Field.register_lookup
class LessThan(Lookup):
    lookup_name = "lt"

    def is_matching(self, field_value: Any, filter_value: Any):
        return field_value < filter_value


@Field.register_lookup
class LessThanOrEqual(Lookup):
    lookup_name = "lte"

    def is_matching(self, field_value: Any, filter_value: Any):
        return field_value <= filter_value


# ------------------------------ Patterns lookup ----------------------------- #


@Field.register_lookup
class Contains(Lookup):
    lookup_name = "contains"

    def is_matching(self, field_value: str, filter_value: str):
        found = field_value.find(filter_value)
        if found == -1:
            return False
        return True


@Field.register_lookup
class IContains(CaseInsensitive, Contains):
    lookup_name = "icontains"


@Field.register_lookup
class StartsWith(Lookup):
    lookup_name = "startswith"

    def is_matching(self, field_value: str, filter_value: str):
        return field_value.startswith(filter_value)


@Field.register_lookup
class IStartsWith(CaseInsensitive, StartsWith):
    lookup_name = "istartswith"


@Field.register_lookup
class EndsWith(Lookup):
    lookup_name = "endswith"

    def is_matching(self, field_value: str, filter_value: str):
        return field_value.endswith(filter_value)


@Field.register_lookup
class IEndsWith(CaseInsensitive, EndsWith):
    lookup_name = "iendswith"


# ----------------------------- ArrayField Lookup ---------------------------- #


class ArrayLookup(Lookup):
    def prepare_filter_value(self, filter_value: Any) -> Any:
        if isinstance(filter_value, str):
            return [filter_value]
        return super().prepare_filter_value(filter_value)

    def prepare_field_value(self, field_value: Any) -> Any:
        return [field.get_value() for field in field_value]


@ArrayField.register_lookup
class ArrayContains(ArrayLookup, Contains):
    def is_matching(self, field_value: str, filter_value: str):
        if all([value in field_value for value in filter_value]):
            return True
        return False


@ArrayField.register_lookup
class ArrayContainedBy(ArrayLookup, Lookup):
    lookup_name = "contained_by"

    def is_matching(self, field_value: str, filter_value: str):
        if all([value in filter_value for value in field_value]):
            return True
        return False


@ArrayField.register_lookup
class ArrayOverlap(ArrayLookup, Lookup):
    lookup_name = "overlap"

    def is_matching(self, field_value: str, filter_value: str):
        for value in filter_value:
            if value in field_value:
                return True
        return False


@ArrayField.register_lookup
class ArrayLength(ArrayLookup):
    lookup_name = "len"
    filter_types = (int,)

    def is_matching(self, field_value: str, filter_value: int):
        return len(field_value) == filter_value


@ArrayField.register_lookup
class ArrayInLookup(ArrayLookup, In):
    def is_matching(self, field_value: Any, filter_value: Iterable):
        matching = False
        for value in field_value:
            matching = super().is_matching(value, filter_value)
            if matching is True:
                break
        return matching


# ------------------------------ Related lookup ------------------------------ #


class RelatedLookup(ArrayInLookup):
    filter_types = (
        list,
        tuple,
        Dataset,
    )

    def prepare_filter_value(self, filter_value: Any) -> Any:
        return filter_value

    def prepare_field_value(self, field_value: Any) -> Any:
        return field_value


@DatasetField.register_lookup
class DatasetInLookup(RelatedLookup, In):
    pass
