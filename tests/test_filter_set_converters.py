"""FilterSet converters tests."""

from anytree import Node
from anytree.exporter import DictExporter
from django.test import TestCase
from graphene_django_filter.filter_set_converters import (
    filter_set_to_trees,
    get_input_type_name,
    sequence_to_tree,
    try_add_sequence,
)

from .filter_set import TaskFilter


class FilterSetConverterTest(TestCase):
    """FilterSet converters tests."""

    def setUp(self) -> None:
        """Set up FilterSet converters tests."""
        self.abstract_tree = Node(
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
        self.task_filter_trees = [
            Node(name='name', children=[Node(name='exact', filter_name='name')]),
            Node(
                name='user', children=[
                    Node(
                        name='last_name', children=[
                            Node(name='exact', filter_name='user__last_name'),
                        ],
                    ),
                    Node(
                        name='email', children=[
                            Node(name='iexact', filter_name='user__email__iexact'),
                            Node(name='contains', filter_name='user__email__contains'),
                            Node(name='icontains', filter_name='user__email__icontains'),
                        ],
                    ),
                ],
            ),
        ]

    def test_get_input_type_name(self) -> None:
        """Test the `get_input_type_name` function."""
        self.assertEqual(
            'TaskUserFirstNameFilterInputType',
            get_input_type_name(
                'TaskType', (Node(name='user'), Node(name='first_name')),
            ),
        )

    def test_filter_set_to_trees(self) -> None:
        """Test the `filter_set_to_trees` function."""
        trees = filter_set_to_trees(TaskFilter)
        exporter = DictExporter()
        self.assertEqual(
            [exporter.export(tree) for tree in self.task_filter_trees],
            [exporter.export(tree) for tree in trees],
        )

    def test_possible_try_add_sequence(self) -> None:
        """Test the `try_add_sequence` function when adding a sequence is possible."""
        is_mutated = try_add_sequence(
            self.abstract_tree, (
                {'name': 'field1'},
                {'name': 'field5'},
                {'name': 'field6'},
            ),
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
            DictExporter().export(self.abstract_tree),
        )

    def test_impossible_try_add_sequence(self) -> None:
        """Test the `try_add_sequence` function when adding a sequence is impossible."""
        is_mutated = try_add_sequence(self.abstract_tree, ({'name': 'field5'}, {'name': 'field6'}))
        self.assertFalse(is_mutated)

    def test_sequence_to_tree(self) -> None:
        """Test the `sequence_to_tree` function."""
        self.assertEqual(
            {
                'name': 'field1',
                'children': [{'name': 'field2'}],
            },
            DictExporter().export(
                sequence_to_tree(
                    ({'name': 'field1'}, {'name': 'field2'}),
                ),
            ),
        )
