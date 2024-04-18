import importlib

from pathlib import Path

import pytest

from datalookup import Dataset, FieldNotFound, FilterDoesNotExist, Node
from datalookup.fields import ArrayField, DatasetField, NodeField, ValueField
from datalookup.lookup import Lookup
from datalookup.utils import REPR_OUTPUT_SIZE, LookupRegistryError, RegisterLookupMixin

# Import lookup here as class lookups are cached on first call
importlib.import_module("tests.lookup")

CURRENT_PATH = Path(__file__).resolve(True).parent


# Collection fixture for filtering tests
@pytest.fixture()
def books():
    json_file = CURRENT_PATH / "data/books.json"
    yield Dataset.from_json(json_file)


# Collection fixture for filtering tests
@pytest.fixture()
def recipe():
    json_file = CURRENT_PATH / "data/recipe.json"
    yield Dataset.from_json(json_file)


class BaseDatasetTests:
    @pytest.mark.parametrize(
        "data", [[{"name": "config_1"}], {"name": "config_1"}], ids=["list", "dict"]
    )
    def test_load_simple_data(self, data):
        """Load a simple set of data"""
        dataset = Dataset(data)
        assert len(dataset) == 1
        assert all([isinstance(n, Node) for n in dataset.nodes])

    @pytest.mark.parametrize("data", [["x", {}], "any"], ids=["list_of_any", "any"])
    def test_create_dataset_from_wrong_type(self, data):
        """
        Raise a ValueError if we try to create a dataset something
        different than a list of dict or a simple dict
        """
        with pytest.raises(ValueError):
            Dataset(data)

    def test_load_from_json_file(self):
        """Load data from a json file"""
        current_path = Path(__file__).resolve(True).parent
        json_file = current_path / "data/books.json"
        dataset = Dataset.from_json(json_file)
        assert len(dataset) == 3

    def test_load_from_nodes(self):
        """Load data from a list of nodes"""

        # nodes must be a list
        with pytest.raises(TypeError):
            Dataset.from_nodes("x")

        # nodes must be a list of nodes
        with pytest.raises(TypeError):
            Dataset.from_nodes(["x"])

        # Check that we correctly load the nodes
        dataset = Dataset.from_nodes([Node({"test": "test"})])
        assert len(dataset) == 1
        assert dataset[0].test == "test"

    def test_dataset_equality(self, books: Dataset):
        """Check the equality of dataset"""
        assert books == books
        assert books[0].books != books
        assert books != "x"

        # Change one value of the books and then compare
        new_books = Dataset(books.values())
        assert new_books == books
        new_books[0].get_field("author").set_value("stephane")
        assert new_books != books

        # Test hashing function
        assert hash(books) == hash(Dataset(books.values()))

    def test_get_values_from_a_dataset(self):
        """Check that we correctly deserialize data"""
        data = [
            {"id": "1", "value": "new"},
            {"id": "2", "value": "open"},
            {"id": "1", "value": "close"},
        ]

        # Create the dataset from the data
        dataset = Dataset(data)
        assert all([isinstance(d, Node) for d in dataset.nodes]) is True
        dataset.values() == data

    def test_dataset_subscriptable(self):
        """Check that we can access a node with [0-X]"""
        dataset = Dataset(
            [
                {"id": "1"},
                {"id": "2"},
            ]
        )
        assert dataset[0].id == "1"

        with pytest.raises(TypeError):
            dataset["x"]

    def test_repr_dataset(self, books: Dataset):
        """Check format of repr(dataset)"""
        repr_value = "<Dataset [<Node: Node object (1)>]>"
        assert repr(books.filter(author="J. K. Rowling")) == repr_value

        # Represent max output size
        data = [{f"name_{i}": i} for i in range(0, REPR_OUTPUT_SIZE + 1)]
        dataset = Dataset(data)
        assert "...(remaining elements truncated)..." in repr(dataset)

    def test_slice_dataset(self, books: Dataset):
        """Check that we can slice a dataset and that negative index is forbidden"""

        # Get first indice of the dataset
        assert books[0].author == "J. K. Rowling"

        # Assert if indice < 0
        with pytest.raises(ValueError):
            books[-1]

        # Assert if one of the indice in the slice is < 0
        with pytest.raises(ValueError):
            books[-1:2]


class BaseNodeTests:
    data = {
        "id": 1,
        "name": "test",
        "configs": {"name": "config_1"},
        "group": ["group_1", "group_2"],
        "modes": [
            {"name": "mode_1"},
            {"name": "mode_2"},
            {"name": "mode_3"},
        ],
    }

    @pytest.fixture(scope="class")
    def node(self):
        yield Node(self.data)

    def test_populate_node(self):
        """Check that we correctly populate a node"""
        node = Node(self.data)

        # Check that we can access fields value using instance attribute
        assert node.id == 1
        assert node.name == "test"

        # Check that we correctly have 5 fields
        assert len(node.fields) == 5

        # Check that we have loaded correct fields
        fields = node.fields.values()
        assert len([f for f in fields if isinstance(f, ValueField)]) == 3
        assert len([f for f in fields if isinstance(f, NodeField)]) == 1
        assert len([f for f in fields if isinstance(f, DatasetField)]) == 1
        assert len([f for f in fields if isinstance(f, ArrayField)]) == 1

        # Check that a wrong data type raise a ValueError
        with pytest.raises(ValueError):
            Node([])

    def test_field_not_found(self, node):
        """Access a field that does not exist"""
        with pytest.raises(FieldNotFound):
            node.get_field("test")

    def test_node_attribute_does_not_exist(self, node):
        """
        Check that None is returned whem trying to access an attribute that
        does not exist
        """
        with pytest.raises(AttributeError):
            node.xxx

    def test_get_node_filters(self, node):
        """Get all filter + related filter in a node"""
        assert node.get_filters() == {
            "id",
            "name",
            "configs",
            "configs__name",
            "group",
            "modes__name",
            "modes",
        }

    def test_get_related_nodes(self, node):
        """Get the list of attributes that contain a node"""
        related_nodes = [
            field.get_name() for field in node.fields.values() if field.has_node()
        ]
        assert related_nodes == ["configs", "modes"]

    def test_equality_between_nodes(self, books: Dataset):
        """Check nodes equality"""
        author = books[0]
        assert author == books[0]
        assert author != "x"
        assert author != books[1]

    def test_node_values(self, node: Node):
        """Check that values() return the same info as the data"""
        assert node.values() == self.data


class BaseFieldTests:
    @pytest.fixture()
    def field(self):
        yield ValueField("type", "cake")

    def test_get_protected_name(self, field):
        """Check that we can correctly get the name of the field"""
        assert field.get_name() == "type"
        assert field.type == "cake"

    def test_check_field_name(self):
        """Check that the name of the field is conform"""
        with pytest.raises(NameError):
            ValueField("name__")
        with pytest.raises(NameError):
            ValueField("config__name")

    def test_get_field_value(self, field):
        """Check that we can access the value of the field"""
        assert field.get_value() == "cake"

    def test_set_field_value(self, field):
        """Check that we can set a new value to the field"""
        assert field.get_value() == "cake"
        field.set_value("apple")
        assert field.get_value() == "apple"

    def test_equality_between_fields(self, field):
        """Check the equality between field"""
        assert ValueField("type", "cake") == field
        assert ValueField("typo", "cake") != field

        # Create dataset field to test related_field
        dataset = DatasetField("dataset", [{"test": "test"}])
        assert dataset != field

        node = NodeField("node", {"test": "test"})
        assert node != dataset

    def test_related_field_has_node(self):
        """Check if related field has a node"""
        dataset = DatasetField("dataset", [{"test": "test"}])
        assert dataset.has_node() is True

    @pytest.mark.parametrize(
        "field,result",
        [
            (ValueField("test", 1), 1),
            (NodeField("test", {"test": "test"}), Node({"test": "test"})),
            (DatasetField("test", [{"test": "test"}]), Dataset([{"test": "test"}])),
        ],
    )
    def test_serialize_field(self, field, result):
        """Check that each field value is serialized"""
        assert field.get_value() == result

    @pytest.mark.parametrize(
        "field,result",
        [
            (ValueField("test", 1), 1),
            (NodeField("test", {"test": "test"}), {"test": "test"}),
            (DatasetField("test", [{"test": "test"}]), [{"test": "test"}]),
        ],
    )
    def test_deserialize_field(self, field, result):
        """Check that each field is well deserialize"""
        assert field.deserialize() == result

    def test_validate_value_field(self):
        """Check that a ValueField only accept type that is not a list or a dict"""
        with pytest.raises(TypeError):
            ValueField("test", value={})
        with pytest.raises(TypeError):
            ValueField("test", value=[])

    def test_validate_array_field(self):
        """Check that an ArrayField only accept list type"""
        with pytest.raises(TypeError):
            ArrayField("test", value={})

    def test_validate_node_field(self):
        """Check thtat a node field only accept dict"""
        with pytest.raises(TypeError):
            NodeField("test", value=[])

    def test_validate_dataset_field(self):
        """
        Check that a dataset field type must be of a dict or a
        list with only dict as values
        """
        with pytest.raises(ValueError):
            DatasetField("test", value=["x"])
        with pytest.raises(TypeError):
            DatasetField("test", value="x")


class FilteringTests:
    def test_filter_dataset_no_filter(self, books: Dataset):
        """Do not pass any filter. Return dataset should be the same"""
        data = books.filter()
        assert isinstance(data, Dataset)
        assert data == data

    def test_simple_filter_not_existing_data(self, books: Dataset, recipe: Dataset):
        """Try to look for data that does not exist"""
        authors = books.filter(author="Not exist")
        assert len(authors) == 0

        # Check not exist with related filter
        authors = books.filter(books__name="Not exist")
        assert len(authors) == 0

        # Check with a deep node filtering and not a deep dataset filtering
        recipes = recipe.filter(batters__batter__type="Not exist")
        assert len(recipes) == 0

    def test_simple_filter(self, books: Dataset):
        """Get the books of a specific author"""
        books = books.filter(author="J. K. Rowling")
        assert len(books) == 1
        assert books[0].author == "J. K. Rowling"
        assert len(books[0].books) == 2
        assert books[0].books[0].name == "Harry Potter and the Chamber of Secrets"

    def test_filter_using_related_node(self, books: Dataset):
        """Get the author for books published at a specific date"""
        authors = books.filter(books__published="1999")
        assert len(authors) == 1
        assert authors[0].author == "J. K. Rowling"
        assert len(authors[0].books) == 2

        # Other check using the genre where we should find two authors
        authors = books.filter(books__genre="Fantasy")
        assert len(authors) == 2

    def test_multiple_filters(self, books: Dataset):
        """Check that we correctly find or not authors with two filters"""
        authors = books.filter(books__genre="Fantasy", books__published="1999")
        assert len(authors) == 1
        assert authors[0].author == "J. K. Rowling"

        # Create a new filter where we should not find any authors
        authors = books.filter(books__genre="Fiction")
        assert len(authors) == 0

    def test_filter_does_not_exist(self, books: Dataset):
        """Check that if we pass a wrong filter we get an Exception raised"""
        with pytest.raises(FilterDoesNotExist):
            books.filter(does_not_exist="mode")

    def test_chaining_filters(self, recipe: Dataset):
        """Chain two filters on one query"""
        recipes = recipe.filter(ppu=0.55).filter(batters__batter__type="Chocolate")
        assert len(recipes) == 1
        assert recipes[0].name == "Old Fashioned"

    def test_exclude(self, books: Dataset):
        """Check that we return all elements that are not exclude"""
        authors = books.exclude(books__genre="Fantasy")
        assert len(authors) == 1
        assert authors[0].author == "Agatha Christie"

    def test_exclude_empty_kwargs(self, books: Dataset):
        """If an empty directory is passed, return the full dataset"""
        authors = books.exclude()
        assert len(authors) == 3

    def test_distinct(self):
        """Check that we correctly remove duplicates"""
        data = [{"test": "test"}, {"test": "test"}, {"hello": "test"}]
        dataset = Dataset(data)
        assert len(dataset) == 3
        distinct_set = dataset.distinct()
        assert len(distinct_set) == 2

    def test_or_between_two_filters(self, books: Dataset):
        """Check that we can execute OR between two filters"""

        # Check that the first filter does not find anything but the second one does
        authors = books.filter(author="Stephane Capponi") | books.filter(
            author="Richard Adams"
        )
        assert len(authors) == 1
        assert authors[0].author == "Richard Adams"

        # Check that both filters match an entry
        authors = books.filter(author="J. K. Rowling") | books.filter(
            author="Richard Adams"
        )
        assert len(authors) == 2
        assert authors[0].author == "J. K. Rowling"
        assert authors[1].author == "Richard Adams"

        # Check that we don't get duplicate if node already exist
        authors = books.filter(author="J. K. Rowling") | books.filter(
            author="J. K. Rowling"
        )
        assert len(authors) == 1

    def test_filtering_on_cascade(self, recipe: Dataset):
        """Filtering with cascade should also filter related fields"""
        recipes = recipe.on_cascade().filter(batters__batter__id="1003")
        assert len(recipes) == 1
        assert len(recipes[0].batters.batter) == 1


class BaseLookupTests:
    def test_lookup_not_subclass_of_lookup(self):
        """Any lookup must be a subclass of Lookup"""

        class Foo:
            pass

        with pytest.raises(LookupRegistryError):
            RegisterLookupMixin.register_lookup(Foo)

    def test_lookup_name_is_none(self):
        """Validated that we can pass a lookup_name in the register_lookup method"""

        class Foo(Lookup):
            pass

        # Register the lookup
        ValueField.register_lookup(Foo, lookup_name="foo_lookup")

        # Chech check that the lookup is in the ValueField
        field = ValueField("test", 1)
        assert "foo_lookup" in field.class_lookups


class LookupFilteringTests:
    @pytest.mark.parametrize(
        "filter",
        [{"books__genre": "Fantasy"}, {"books__genre__exact": "Fantasy"}],
        ids=["no_lookup", "exact_lookup"],
    )
    def test_lookup_exact(self, books: Dataset, filter: dict):
        """Check the default '__exact' lookup"""
        authors = books.filter(**filter)
        assert len(authors) == 2
        assert authors[0].books[0].name == "Harry Potter and the Chamber of Secrets"

    def test_lookup_iexact(self, books: Dataset):
        """Check the default '__iexact' lookup"""
        # Show that exact, is case sensitive
        authors = books.filter(books__genre__exact="fantasy")
        assert len(authors) == 0

        # Use iexact for case insensitive
        authors = books.filter(books__genre__iexact="fantasy")
        assert len(authors) == 2

    def test_lookup_in(self, books):
        """Check the '__in' lookup"""
        authors = books.filter(author__in=["Richard Adams", "Agatha Christie"])
        assert len(authors) == 2

    def test_lookup_in_filter_value_type_error(self, books: Dataset):
        """Check that we give an iterable to the '__in' parameter filter"""
        with pytest.raises(TypeError):
            books.filter(author__in=12)

    def test_lookup_regex(self, books: Dataset):
        """Check the '__regex' lookup"""
        authors = books.filter(author__regex=r".*R.*")
        assert len(authors) == 2

    def test_lookup_iregex(self, books: Dataset):
        """Check the '__iregex' lookup"""
        authors = books.filter(author__iregex=r".*r.*")
        assert len(authors) == 3

    @pytest.mark.parametrize(
        "lookup, result",
        [
            ("contains", [2]),
            ("icontains", [0, 2]),
            ("startswith", [2]),
            ("istartswith", [2]),
            ("endswith", []),
            ("iendswith", []),
        ],
    )
    def test_pattern_lookups_with_substr(
        self, books: Dataset, lookup: str, result: int
    ):
        """Check pattern lookup like '__startswith, __endswith..'"""
        authors = books.filter(**{f"books__name__{lookup}": "And"})
        assert len(authors) == len(result)
        for author_index in result:
            assert books[author_index] in authors

    def test_lookup_gt(self, books: Dataset):
        """Test greater than lookup"""
        authors = books.filter(id__gt=2)
        assert len(authors) == 1
        assert authors[0].author == "Agatha Christie"

    def test_lookup_gte(self, books: Dataset):
        """Test greater than or equal lookup"""
        authors = books.filter(id__gte=2)
        assert len(authors) == 2
        assert authors[0].author == "Richard Adams"
        assert authors[1].author == "Agatha Christie"

    def test_lookup_lt(self, books: Dataset):
        """Test lower than lookup"""
        authors = books.filter(id__lt=2)
        assert len(authors) == 1
        assert authors[0].author == "J. K. Rowling"

    def test_lookup_lte(self, books: Dataset):
        """Test lower than or equal lookup"""
        authors = books.filter(id__lte=2)
        assert len(authors) == 2
        assert authors[0].author == "J. K. Rowling"
        assert authors[1].author == "Richard Adams"

    def test_lookup_comparison_wrong_type(self, books: Dataset):
        """Check that the value type must match the filter value type"""
        with pytest.raises(TypeError):
            books.filter(id__gt="x")

    def test_lookup_not_exist(self, books):
        """Raise an error when the lookup does not exist"""
        with pytest.raises(LookupError):
            books.filter(author__xxx="1")

    def test_create_new_lookup(self, books):
        """Create a new lookup based on the Lookup class"""
        # As FooLookup return True, it does not filter so we should
        # get all the configs
        authors = books.filter(author__foo="1")
        assert len(authors) == 3

    def test_lookup_range(self, books: Dataset):
        """Check the range lookup"""
        authors = books.filter(id__range=(0, 3))
        assert len(authors) == 2

    def test_isnull_lookup(self, recipe: Dataset):
        """Return value that are null or not"""
        recipes = recipe.filter(time__isnull=True)
        assert len(recipes) == 2
        recipes = recipe.filter(time__isnull=False)
        assert len(recipes) == 1


class ArrayLookupTests:
    def test_array_contains_lookup(self, recipe: Dataset):
        """Check iterable lookup with an iterable node field value"""
        recipes = recipe.filter(topping__contains="Glazed")
        assert len(recipes) == 2
        recipes = recipe.filter(topping__contains=["Sugar", "Glazed"])
        assert len(recipes) == 1

    def test_array_contained_by_lookup(self, recipe: Dataset):
        """Check iterable lookup with an iterable node field value"""
        recipes = recipe.filter(topping__contained_by=["Glazed", "Sugar"])
        assert len(recipes) == 2
        recipes = recipe.filter(topping__contained_by=["Sugar", "Glazed", "Chocolate"])
        assert len(recipes) == 3

    def test_array_overlap_lookup(self, recipe: Dataset):
        """Check iterable lookup with an iterable node field value"""
        recipes = recipe.filter(topping__overlap=["Glazed", "Sugar"])
        assert len(recipes) == 3
        recipes = recipe.filter(topping__overlap=["Glazed"])
        assert len(recipes) == 2

    def test_array_len_lookup(self, recipe: Dataset):
        """Check iterable lookup with an iterable node field value"""
        recipes = recipe.filter(topping__len=1)
        assert len(recipes) == 1
        recipes = recipe.filter(topping__len=2)
        assert len(recipes) == 2

    def test_array_in_lookup(self, recipe: Dataset):
        """Check the '__in' lookup for an ArrayField"""
        recipes = recipe.filter(topping__in=["Glazed"])
        assert len(recipes) == 2


class RelatedLookupTests:
    def test_search_related_field(self, recipe: Dataset):
        """
        Check that the search method return a list of all nodes for
        a specific related node
        """
        batters = recipe._search_related_node("batters.batter", recipe.nodes)
        assert len(batters) == 7
        assert batters[0].id == "1001"

    def test_filter_related(self, recipe: Dataset):
        """Check that we can correctly filter a related node"""
        batters = recipe.filter_related(name="batters.batter", type="Regular")
        assert len(batters) == 3

    @pytest.mark.parametrize(
        "batter, result", [("Regular", 3), ("Chocolate", 2), ("Blueberry", 1)]
    )
    def test_related_in(self, recipe: Dataset, batter, result):
        """Test that we can filter using a related dataset"""
        recipes = recipe.filter(
            batters__batter__in=recipe.filter_related(
                name="batters.batter", type=batter
            )
        )
        assert len(recipes) == result

    @pytest.mark.parametrize(
        "batter, result", [("Regular", 0), ("Chocolate", 1), ("Blueberry", 2)]
    )
    def test_exclude_related_in(self, recipe: Dataset, batter, result):
        """Check that we can exclude with a related dataset"""
        recipes = recipe.exclude(
            batters__batter__in=recipe.filter_related(
                name="batters.batter", type=batter
            )
        )
        assert len(recipes) == result

    def test_related_exact(self, recipe: Dataset):
        """Check the '__exact' lookup with a dataset as a filter value"""
        recipes = recipe.filter(
            batters__batter=Dataset({"id": "1001", "type": "Regular"})
        )
        assert len(recipes) == 1
        assert recipes[0].name == "Raised"
