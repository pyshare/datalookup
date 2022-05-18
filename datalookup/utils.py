from __future__ import annotations

import functools
import inspect

from typing import TYPE_CHECKING, Optional, Type

from datalookup.exceptions import LookupRegistryError

if TYPE_CHECKING:  # pragma: no cover
    from datalookup.lookup import Lookup

# Separator used to split filter strings apart.
LOOKUP_SEP = "__"

# The maximum number of items to display in a Dataset.__repr__
REPR_OUTPUT_SIZE = 20


class RegisterLookupMixin:
    """Base class to register lookup"""

    @classmethod
    def _get_lookup(cls, lookup_name: str) -> Type[Lookup]:
        return cls.get_lookups().get(lookup_name, None)

    @classmethod
    @functools.lru_cache()
    def get_lookups(cls) -> dict:
        class_lookups = [
            parent.__dict__.get("class_lookups", {}) for parent in inspect.getmro(cls)
        ]
        return cls.merge_dicts(class_lookups)

    def get_lookup(self, lookup_name: str) -> Type[Lookup]:
        return self._get_lookup(lookup_name)

    @classmethod
    def register_lookup(cls, lookup: Type[Lookup], lookup_name: Optional[str] = None):
        from datalookup.lookup import Lookup

        if not issubclass(lookup, Lookup):
            raise LookupRegistryError(f"'{lookup}' is not a subclass of Lookup")
        if lookup_name is None:
            lookup_name = lookup.lookup_name
        if "class_lookups" not in cls.__dict__:
            cls.class_lookups = {}
        cls.class_lookups[lookup_name] = lookup
        return lookup

    @staticmethod
    def merge_dicts(dicts):
        """
        Merge dicts in reverse to preference the order of the original list. e.g.,
        merge_dicts([a, b]) will preference the keys in 'a' over those in 'b'.
        """
        merged = {}
        for d in reversed(dicts):
            merged.update(d)
        return merged


def hash_list(items: list) -> int:
    """Create a hash from element in a list"""
    hash_list = []
    for element in items:
        hash_list.append(hash(element))
    return hash("-".join([str(i) for i in sorted(hash_list)]))
