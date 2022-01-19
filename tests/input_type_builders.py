"""Input filter types builders tests."""

import graphene
from django.test import TestCase
from graphene_django_filter.input_type_builders import LookupInputTypeBuilder


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
