"""FilterSet converters tests."""

from anytree import Node
from anytree.exporter import DictExporter
from django.test import TestCase
from graphene_django_filter.filter_set_converters import (
    filter_set_to_trees,
    sequence_to_tree,
    try_add_sequence,
)

from .filter_set import TaskFilter


class FilterSetConverterTest(TestCase):
    """FilterSet converters tests."""

    def setUp(self) -> None:
        """Set up TreeFunctions tests."""
        self.tree = Node(
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

    def test_list_to_tree(self) -> None:
        """Test the sequence_to_tree function."""
        self.assertEqual(
            DictExporter().export(sequence_to_tree(('field1', 'field2'))),
            {
                'name': 'field1',
                'children': [{'name': 'field2'}],
            },
        )

    def test_possible_try_add_iterable(self) -> None:
        """Test the try_add_sequence function when adding a sequence is possible."""
        is_mutated = try_add_sequence(self.tree, ('field1', 'field5', 'field6'))
        self.assertEqual(is_mutated, True)
        self.assertEqual(
            DictExporter().export(self.tree), {
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
        )

    def test_impossible_try_add_iterable(self) -> None:
        """Test the try_add_sequence function when adding a sequence is impossible."""
        is_mutated = try_add_sequence(self.tree, ('field5', 'field6'))
        self.assertEqual(is_mutated, False)

    def test_filter_set_to_trees(self) -> None:
        """Test the filter_set_to_trees function."""
        trees = filter_set_to_trees(TaskFilter)
        exporter = DictExporter()
        self.assertEqual(
            [exporter.export(tree) for tree in trees], [
                {
                    'name': 'name',
                    'children': [{'name': 'exact'}],
                },
                {
                    'name': 'user',
                    'children': [
                        {
                            'name': 'last_name',
                            'children': [{'name': 'exact'}],
                        },
                        {
                            'name': 'email',
                            'children': [{'name': 'exact'}, {'name': 'contains'}],
                        },
                    ],
                },
            ],
        )
