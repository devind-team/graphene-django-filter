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
        'exact': graphene.String,
        'iexact': graphene.String,
        'contains': graphene.String,
        'icontains': graphene.String,
        'gt': graphene.Float,
        'gte': graphene.Float,
        'lt': graphene.Float,
        'lte': graphene.Float,
    }

    def setUp(self) -> None:
        """Set up LookupInputTypeBuilder tests."""
        self.builder = LookupInputTypeBuilder(
            'User', 'first_name',
        )

    def test_name(self) -> None:
        """Test that LookupInputType will be created with the correct name."""
        input_type = self.builder.build()
        self.assertEqual(input_type.__name__, 'UserFirstNameFilterInputType')

    def test_exact(self) -> None:
        """Test LookupInputType creation with exact field."""
        input_type = self.builder.set_exact().build()
        self.assertIs(type(getattr(input_type, 'exact')), graphene.String)
        self.assertEqual(
            getattr(input_type, 'exact').kwargs, {
                'description': 'exact lookup',
            },
        )

    def test_simple(self) -> None:
        """Test LookupInputType creation with simple fields."""
        builder = self.builder
        for lookup in self._simple_lookups:
            builder = getattr(builder, f'set_{lookup}')()
        input_type = builder.build()
        for lookup, field_type in self._simple_lookups.items():
            with self.subTest(input_type=input_type, lookup=lookup, field_type=field_type):
                self.assertIs(type(getattr(input_type, lookup)), field_type)
                self.assertEqual(
                    getattr(input_type, lookup).kwargs, {
                        'description': f'{lookup} lookup',
                    },
                )

    def test_string_in(self) -> None:
        """Test LookupInputType creation with in of string type field."""
        input_type = self.builder.set_in(is_string=True).build()
        self.assertEqual(type(getattr(input_type, 'in')), graphene.String)
        self.assertEqual(
            getattr(input_type, 'in').kwargs, {
                'description': 'in lookup',
            },
        )

    def test_float_list_in(self) -> None:
        """Test LookupInputType creation with in of list of float type field."""
        input_type = self.builder.set_in(graphene.Float).build()
        in_field = getattr(input_type, 'in')
        self.assertEqual(type(in_field), graphene.List)
        self.assertEqual(in_field.of_type, graphene.Float)
        self.assertEqual(
            getattr(input_type, 'in').kwargs, {
                'description': 'in lookup',
            },
        )


class FilterInputTypeBuilderTest(TestCase):
    """FilterInputTypeBuilder tests."""

    def setUp(self) -> None:
        """Set up FilterInputTypeBuilder tests."""
        self.type_name = 'User'
        self.field1_name = 'first_name'
        self.field1 = LookupInputTypeBuilder(self.type_name, self.field1_name)\
            .set_exact()\
            .set_contains()\
            .build()
        self.field2_name = 'age'
        self.field2 = LookupInputTypeBuilder(self.type_name, self.field2_name)\
            .set_exact()\
            .set_gt()\
            .set_lt()\
            .build()
        self.builder = FilterInputTypeBuilder(self.type_name)

    def test_base(self) -> None:
        """Test FilterInputType creation without any boolean operation fields."""
        input_type = self.builder.add_lookup_input_type(self.field1_name, self.field1)\
            .add_lookup_input_type(self.field2_name, self.field2)\
            .build()
        self.assertEqual(input_type.__name__, f'{self.type_name}FilterInputType')
        self.assertEqual(type(getattr(input_type, self.field1_name)), graphene.Field)
        self.assertEqual(type(getattr(input_type, self.field2_name)), graphene.Field)

    def test_or(self) -> None:
        """Test FilterInputType creation with or field."""
        input_type = self.builder.add_lookup_input_type(self.field1_name, self.field1)\
            .set_or(True)\
            .build()
        self.assertEqual(type(getattr(input_type, 'or')), graphene.Field)
        self.assertEqual(getattr(input_type, 'or').type, input_type)

    def test_and(self) -> None:
        """Test FilterInputType creation with and field."""
        input_type = self.builder.add_lookup_input_type(self.field1_name, self.field1)\
            .set_and(True)\
            .build()
        self.assertEqual(type(getattr(input_type, 'and')), graphene.Field)
        self.assertEqual(getattr(input_type, 'and').type, input_type)
