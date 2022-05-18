"""Global Datalookup exception and warning classes"""


class FilterDoesNotExist(Exception):
    """Raised when a filter does not exist"""


class ObjectNotFound(Exception):
    """Raised when we can't find a value assciated to a given filter"""


class FieldNotFound(Exception):
    """Raised when a field is not found in a Node"""


class LookupRegistryError(Exception):
    """
    Exception raised when we try to register a
    lookup that is not a subclass of Lookup
    """
