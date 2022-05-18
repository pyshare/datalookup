from datalookup.fields import Field
from datalookup.lookup import Lookup


@Field.register_lookup
class FooLookup(Lookup):
    lookup_name = "foo"

    def is_matching(self, filter_value, node_value):
        return True
