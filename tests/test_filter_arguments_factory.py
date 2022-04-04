"""Tests for converting a AdvancedFilterSet class to filter arguments."""

from unittest.mock import patch

import graphene
from anytree import Node
from anytree.exporter import DictExporter
from django.test import TestCase
from graphene_django_filter.filter_arguments_factory import FilterArgumentsFactory
from graphene_django_filter.input_types import (
    SearchQueryFilterInputType,
    SearchRankFilterInputType,
    TrigramFilterInputType,
)
from stringcase import pascalcase

from .filtersets import TaskFilter


class FilterArgumentsFactoryTests(TestCase):
    """The `FilterArgumentsFactory` class tests."""

    abstract_tree_root = Node(
        'field1', children=(
            Node(
                'field2', children=(
                    Node(
                        'field3', children=(
                            Node('field4'),
                        ),
                    ),
                ),
            ),
        ),
    )
    task_filter_trees_roots = [
        Node(
            name='name', children=[
                Node(name='exact'),
                Node(name='contains'),
                Node(
                    name='trigram', children=[
                        Node(name='exact'),
                        Node(name='gt'),
                        Node(name='gte'),
                        Node(name='lt'),
                        Node(name='lte'),
                    ],
                ),
            ],
        ),
        Node(name='created_at', children=[Node(name='gt')]),
        Node(name='completed_at', children=[Node(name='lt')]),
        Node(name='description', children=[Node(name='exact'), Node(name='contains')]),
        Node(
            name='user', children=[
                Node(name='exact'),
                Node(name='in'),
                Node(
                    name='email', children=[
                        Node(name='exact'),
                        Node(name='iexact'),
                        Node(name='contains'),
                        Node(name='icontains'),
                    ],
                ),
                Node(
                    name='last_name', children=[
                        Node(name='exact'),
                        Node(name='contains'),
                    ],
                ),
            ],
        ),
        Node(name='search_query', children=[Node(name='exact')]),
        Node(
            name='search_rank', children=[
                Node(name='exact'),
                Node(name='gt'),
                Node(name='gte'),
                Node(name='lt'),
                Node(name='lte'),
            ],
        ),
    ]

    def test_sequence_to_tree(self) -> None:
        """Test the `sequence_to_tree` method."""
        self.assertEqual(
            {
                'name': 'field1',
                'children': [{'name': 'field2'}],
            },
            DictExporter().export(FilterArgumentsFactory.sequence_to_tree(('field1', 'field2'))),
        )

    def test_possible_try_add_sequence(self) -> None:
        """Test the `try_add_sequence` method when adding a sequence is possible."""
        is_mutated = FilterArgumentsFactory.try_add_sequence(
            self.abstract_tree_root, ('field1', 'field5', 'field6'),
        )
        self.assertTrue(is_mutated)
        self.assertEqual(
            {
                'name': 'field1',
                'children': [
                    {
                        'name': 'field2',
                        'children': [
                            {
                                'name': 'field3',
                                'children': [{'name': 'field4'}],
                            },
                        ],
                    },
                    {
                        'name': 'field5',
                        'children': [{'name': 'field6'}],
                    },
                ],
            },
            DictExporter().export(self.abstract_tree_root),
        )

    def test_impossible_try_add_sequence(self) -> None:
        """Test the `try_add_sequence` method when adding a sequence is impossible."""
        is_mutated = FilterArgumentsFactory.try_add_sequence(
            self.abstract_tree_root, ('field5', 'field6'),
        )
        self.assertFalse(is_mutated)

    def test_init(self) -> None:
        """The the `__init__` method."""
        filter_arguments_factory = FilterArgumentsFactory(TaskFilter, 'Task')
        self.assertEqual(TaskFilter, filter_arguments_factory.filterset_class)
        self.assertEqual('Task', filter_arguments_factory.input_type_prefix)
        self.assertEqual('TaskFilterInputType', filter_arguments_factory.filter_input_type_name)

    def test_filterset_to_trees(self) -> None:
        """Test the `filterset_to_trees` method."""
        roots = FilterArgumentsFactory.filterset_to_trees(TaskFilter)
        exporter = DictExporter()
        self.assertEqual(
            [exporter.export(root) for root in self.task_filter_trees_roots],
            [exporter.export(root) for root in roots],
        )

    def test_create_input_object_type(self) -> None:
        """Test the `create_input_object_type` method."""
        input_object_type = FilterArgumentsFactory.create_input_object_type(
            'CustomInputObjectType',
            {'field': graphene.String()},
        )
        self.assertEqual('CustomInputObjectType', input_object_type.__name__)
        self.assertTrue(issubclass(input_object_type, graphene.InputObjectType))
        self.assertTrue(hasattr(input_object_type, 'field'))

    @patch(
        'graphene_django_filter.filter_arguments_factory.FilterArgumentsFactory.input_object_types',
        new={},
    )
    def test_create_input_object_type_cache(self) -> None:
        """Test the `create_input_object_type` method's cache usage."""
        self.assertEqual({}, FilterArgumentsFactory.input_object_types)
        key = 'CustomInputObjectType'
        input_object_type = FilterArgumentsFactory.create_input_object_type(key, {})
        self.assertTrue(
            input_object_type == FilterArgumentsFactory.create_input_object_type(key, {}),
        )
        self.assertEqual({key: input_object_type}, FilterArgumentsFactory.input_object_types)

    def test_create_filter_input_subfield_without_special(self) -> None:
        """Test the `create_filter_input_subfield` method without any special filters."""
        filter_arguments_factory = FilterArgumentsFactory(TaskFilter, 'Task')
        input_field = filter_arguments_factory.create_filter_input_subfield(
            self.task_filter_trees_roots[4],
            'Task',
            'User field',
        )
        self.assertEqual('User field', input_field.description)
        input_object_type = input_field.type
        self.assertEqual('TaskUserFilterInputType', input_object_type.__name__)
        self.assertEqual('`Exact` lookup', getattr(input_object_type, 'exact').description)
        self.assertEqual('`LastName` subfield', getattr(input_object_type, 'last_name').description)
        self.assertEqual('`Email` subfield', getattr(input_object_type, 'email').description)
        email_type = getattr(input_object_type, 'email').type
        self.assertEqual('TaskUserEmailFilterInputType', email_type.__name__)
        for attr in ('iexact', 'contains', 'icontains'):
            self.assertEqual(f'`{pascalcase(attr)}` lookup', getattr(email_type, attr).description)

    def test_create_filter_input_subfield_with_search_query(self) -> None:
        """Test the `create_filter_input_subfield` method with the search query filter."""
        filter_arguments_factory = FilterArgumentsFactory(TaskFilter, 'Task')
        search_query_type = filter_arguments_factory.create_filter_input_subfield(
            self.task_filter_trees_roots[5],
            'Task',
            'SearchQuery',
        ).type
        self.assertEqual(search_query_type, SearchQueryFilterInputType)

    def test_create_filter_input_subtype_with_search_rank(self) -> None:
        """Test the `create_filter_input_subtype` method with the search rank filter."""
        filter_arguments_factory = FilterArgumentsFactory(TaskFilter, 'Task')
        search_rank_type = filter_arguments_factory.create_filter_input_subfield(
            self.task_filter_trees_roots[6],
            'Task',
            'SearchRank',
        ).type
        self.assertEqual(search_rank_type, SearchRankFilterInputType)

    def test_create_filter_input_subtype_with_trigram(self) -> None:
        """Test the `create_filter_input_subtype` method with the trigram filter."""
        filter_arguments_factory = FilterArgumentsFactory(TaskFilter, 'Task')
        input_object_type = filter_arguments_factory.create_filter_input_subfield(
            self.task_filter_trees_roots[0],
            'Task',
            'Name field',
        ).type
        trigram_type = getattr(input_object_type, 'trigram').type
        self.assertEqual(trigram_type, TrigramFilterInputType)

    def test_create_filter_input_type(self) -> None:
        """Test the `create_filter_input_type` method."""
        filter_arguments_factory = FilterArgumentsFactory(TaskFilter, 'Task')
        input_object_type = filter_arguments_factory.create_filter_input_type(
            self.task_filter_trees_roots,
        )
        self.assertEqual('TaskFilterInputType', input_object_type.__name__)
        for attr in ('name', 'description', 'user', 'created_at', 'completed_at'):
            self.assertEqual(
                f'`{pascalcase(attr)}` field',
                getattr(input_object_type, attr).description,
            )
        for operator in ('and', 'or'):
            operator_input_type = getattr(input_object_type, operator)
            self.assertEqual(f'`{operator.capitalize()}` field', operator_input_type.description)
            self.assertIsInstance(operator_input_type.type, graphene.List)
            self.assertEqual(input_object_type, operator_input_type.type.of_type)
        not_input_type = getattr(input_object_type, 'not')
        self.assertEqual('`Not` field', not_input_type.description)
        self.assertEqual(input_object_type, not_input_type.type)

    def test_arguments(self) -> None:
        """Test the `arguments` property."""
        filter_arguments_factory = FilterArgumentsFactory(TaskFilter, 'Task')
        arguments = filter_arguments_factory.arguments
        self.assertEqual(('filter',), tuple(arguments.keys()))
        self.assertEqual('TaskFilterInputType', arguments['filter'].type.__name__)
