"""Input filter types builders tests."""
import graphene
from django.test import TestCase
from graphene_django_filter.input_type_builders import (
    FilterInputTypeBuilder,
    LookupInputTypeBuilder,
)


class LookupInputTypeBuilderTest(TestCase):
    """LookupInputTypeBuilder tests."""

    _simple_lookups = {
        **{
            lookup: {'method': 'set_str_lookup', 'field_type': graphene.String}
            for lookup in LookupInputTypeBuilder.str_lookups
        },
        **{
            lookup: {'method': 'set_float_lookup', 'field_type': graphene.Float}
            for lookup in LookupInputTypeBuilder.float_lookups
        },
    }

    def setUp(self) -> None:
        """Set up LookupInputTypeBuilder tests."""
        self.builder = LookupInputTypeBuilder(
            'User', 'first_name',
        )

    def test_name(self) -> None:
        """Test that LookupInputType will be created with the correct name."""
        input_type = self.builder.build()
        self.assertEqual('UserFirstNameFilterInputType', input_type.__name__)

    def test_subfield(self) -> None:
        """Test LookupInputType creation with subfield."""
        input_type = self.builder.add_subfield(
            'task',
            LookupInputTypeBuilder('UserTask', 'name').build(),
        ).build()
        self.assertIs(graphene.Field, type(getattr(input_type, 'task')))
        self.assertEqual('UserTaskNameFilterInputType', getattr(input_type, 'task').type.__name__)

    def test_exact(self) -> None:
        """Test LookupInputType creation with exact field."""
        input_type = self.builder.set_exact(graphene.Boolean).build()
        self.assertIs(graphene.Boolean, type(getattr(input_type, 'exact')))
        self.assertEqual(
            {'description': 'exact lookup'},
            getattr(input_type, 'exact').kwargs,
        )

    def test_string_in(self) -> None:
        """Test LookupInputType creation with in of string type field."""
        input_type = self.builder.set_in(is_string=True).build()
        self.assertIs(graphene.String, type(getattr(input_type, 'in')))
        self.assertEqual(
            {'description': 'in lookup'},
            getattr(input_type, 'in').kwargs,
        )

    def test_float_list_in(self) -> None:
        """Test LookupInputType creation with in of list of float type field."""
        input_type = self.builder.set_in(graphene.Float).build()
        in_field = getattr(input_type, 'in')
        self.assertIs(graphene.List, type(in_field))
        self.assertIs(graphene.Float, in_field.of_type)
        self.assertEqual(
            {'description': 'in lookup'},
            getattr(input_type, 'in').kwargs,
        )

    def test_invalid_str_lookup(self) -> None:
        """Test set_str_lookup method call with invalid lookup."""
        self.assertRaises(
            AssertionError,
            lambda: self.builder.set_str_lookup('invalid_lookup'),
        )

    def test_invalid_float_lookup(self) -> None:
        """Test set_float_lookup method call with invalid lookup."""
        self.assertRaises(
            AssertionError,
            lambda: self.builder.set_float_lookup('invalid_lookup'),
        )

    def test_simple(self) -> None:
        """Test LookupInputType creation with simple fields."""
        builder = self.builder
        for lookup, data in self._simple_lookups.items():
            builder = getattr(builder, data['method'])(lookup)
        input_type = builder.build()
        for lookup, data in self._simple_lookups.items():
            with self.subTest(input_type=input_type, lookup=lookup, data=data):
                self.assertIs(data['field_type'], type(getattr(input_type, lookup)))
                self.assertEqual(
                    {'description': f'{lookup} lookup'},
                    getattr(input_type, lookup).kwargs,
                )


class FilterInputTypeBuilderTest(TestCase):
    """FilterInputTypeBuilder tests."""

    def setUp(self) -> None:
        """Set up FilterInputTypeBuilder tests."""
        self.type_name = 'User'
        self.field1_name = 'first_name'
        self.field1 = LookupInputTypeBuilder(self.type_name, self.field1_name)\
            .set_exact()\
            .set_str_lookup('contains')\
            .build()
        self.field2_name = 'age'
        self.field2 = LookupInputTypeBuilder(self.type_name, self.field2_name)\
            .set_exact()\
            .set_float_lookup('gt')\
            .set_float_lookup('lt')\
            .build()
        self.builder = FilterInputTypeBuilder(self.type_name)

    def test_base(self) -> None:
        """Test FilterInputType creation without any boolean operation fields."""
        input_type = self.builder.add_lookup_input_type(self.field1_name, self.field1)\
            .add_lookup_input_type(self.field2_name, self.field2)\
            .build()
        self.assertEqual(f'{self.type_name}FilterInputType', input_type.__name__)
        self.assertIs(graphene.Field, type(getattr(input_type, self.field1_name)))
        self.assertIs(graphene.Field, type(getattr(input_type, self.field2_name)))

    def test_or(self) -> None:
        """Test FilterInputType creation with or field."""
        input_type = self.builder.add_lookup_input_type(self.field1_name, self.field1)\
            .set_or(True)\
            .build()
        self.assertIs(graphene.Field, type(getattr(input_type, 'or')))
        self.assertIs(input_type, getattr(input_type, 'or').type)

    def test_and(self) -> None:
        """Test FilterInputType creation with and field."""
        input_type = self.builder.add_lookup_input_type(self.field1_name, self.field1)\
            .set_and(True)\
            .build()
        self.assertIs(graphene.Field, type(getattr(input_type, 'and')))
        self.assertIs(input_type, getattr(input_type, 'and').type)
