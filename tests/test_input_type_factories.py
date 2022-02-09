"""Input type factories tests."""

import graphene
from anytree import Node
from anytree.exporter import DictExporter
from django.test import TestCase
from graphene_django_filter.input_type_factories import (
    create_filter_input_subtype,
    create_filter_input_type,
    create_input_object_type,
    filterset_to_trees,
    get_filtering_args_from_filterset,
    sequence_to_tree,
    try_add_sequence,
)
from stringcase import pascalcase

from .filtersets import TaskFilter
from .object_types import TaskFilterSetClassType


class InputTypeBuildersTest(TestCase):
    """Input type factories tests."""

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
        Node(name='name', children=[Node(name='exact'), Node(name='contains')]),
        Node(name='created_at', children=[Node(name='gt')]),
        Node(name='completed_at', children=[Node(name='lt')]),
        Node(name='description', children=[Node(name='exact'), Node(name='contains')]),
        Node(
            name='user', children=[
                Node(name='exact'),
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
    ]

    def test_sequence_to_tree(self) -> None:
        """Test the `sequence_to_tree` function."""
        self.assertEqual(
            {
                'name': 'field1',
                'children': [{'name': 'field2'}],
            },
            DictExporter().export(sequence_to_tree(('field1', 'field2'))),
        )

    def test_possible_try_add_sequence(self) -> None:
        """Test the `try_add_sequence` function when adding a sequence is possible."""
        is_mutated = try_add_sequence(self.abstract_tree_root, ('field1', 'field5', 'field6'))
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
        """Test the `try_add_sequence` function when adding a sequence is impossible."""
        is_mutated = try_add_sequence(self.abstract_tree_root, ('field5', 'field6'))
        self.assertFalse(is_mutated)

    def test_filterset_to_trees(self) -> None:
        """Test the `filterset_to_trees` function."""
        roots = filterset_to_trees(TaskFilter)
        exporter = DictExporter()
        self.assertEqual(
            [exporter.export(root) for root in self.task_filter_trees_roots],
            [exporter.export(root) for root in roots],
        )

    def test_create_input_object_type(self) -> None:
        """Test the `create_input_object_type` function."""
        input_object_type = create_input_object_type(
            'CustomInputObjectType',
            {'field': graphene.String()},
        )
        self.assertEqual('CustomInputObjectType', input_object_type.__name__)
        self.assertTrue(issubclass(input_object_type, graphene.InputObjectType))
        self.assertTrue(hasattr(input_object_type, 'field'))

    def test_create_filter_input_subtype(self) -> None:
        """Test the `create_filter_input_subtype` function."""
        input_object_type = create_filter_input_subtype(
            self.task_filter_trees_roots[4],
            TaskFilter,
            'Task',
        )
        self.assertEqual('TaskUserFilterInputType', input_object_type.__name__)
        self.assertEqual('`Exact` lookup', getattr(input_object_type, 'exact').description)
        self.assertEqual('`LastName` subfield', getattr(input_object_type, 'last_name').description)
        self.assertEqual('`Email` subfield', getattr(input_object_type, 'email').description)
        email_type = getattr(input_object_type, 'email').type
        self.assertEqual('TaskUserEmailFilterInputType', email_type.__name__)
        for attr in ('iexact', 'contains', 'icontains'):
            self.assertEqual(f'`{pascalcase(attr)}` lookup', getattr(email_type, attr).description)

    def test_create_filter_input_type(self) -> None:
        """Test the `create_filter_input_type` function."""
        input_object_type = create_filter_input_type(
            self.task_filter_trees_roots,
            TaskFilter,
            'Task',
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

    def test_get_filtering_args_from_filterset(self) -> None:
        """Test the `get_filtering_args_from_filterset` function."""
        filtering_args = get_filtering_args_from_filterset(TaskFilter, TaskFilterSetClassType)
        self.assertEqual(('filter',), tuple(filtering_args.keys()))
        self.assertEqual(
            'TaskFilterSetClassFilterInputType',
            filtering_args['filter'].type.__name__,
        )
