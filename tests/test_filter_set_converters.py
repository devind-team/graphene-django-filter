"""FilterSet converters tests."""

from anytree import Node
from anytree.exporter import DictExporter
from django.test import TestCase
from graphene_django_filter.filter_set_converters import (
    create_field_filter_input_type,
    create_filter_input_subtype,
    create_filter_input_type,
    filter_set_to_trees,
    sequence_to_tree,
    try_add_sequence,
)

from .filter_set import TaskFilter


class FilterSetConverterTest(TestCase):
    """FilterSet converters tests."""

    def setUp(self) -> None:
        """Set up FilterSet converters tests."""
        self.abstract_tree_root = Node(
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
        self.task_filter_trees_roots = [
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

    def test_possible_try_add_sequence(self) -> None:
        """Test the `try_add_sequence` function when adding a sequence is possible."""
        is_mutated = try_add_sequence(
            self.abstract_tree_root, (
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
            DictExporter().export(self.abstract_tree_root),
        )

    def test_impossible_try_add_sequence(self) -> None:
        """Test the `try_add_sequence` function when adding a sequence is impossible."""
        is_mutated = try_add_sequence(
            self.abstract_tree_root,
            ({'name': 'field5'}, {'name': 'field6'}),
        )
        self.assertFalse(is_mutated)

    def test_filter_set_to_trees(self) -> None:
        """Test the `filter_set_to_trees` function."""
        roots = filter_set_to_trees(TaskFilter)
        exporter = DictExporter()
        self.assertEqual(
            [exporter.export(root) for root in self.task_filter_trees_roots],
            [exporter.export(root) for root in roots],
        )

    def test_create_field_filter_input_type(self) -> None:
        """Test the `create_field_filter_input_type` function."""
        input_object_type = create_field_filter_input_type(
            self.task_filter_trees_roots[1].children[1],
            TaskFilter,
            'TaskUser',
        )
        self.assertEqual('TaskUserEmailFieldFilterInputType', input_object_type.__name__)
        self.assertTrue(hasattr(input_object_type, 'iexact'))
        self.assertTrue(hasattr(input_object_type, 'contains'))
        self.assertTrue(hasattr(input_object_type, 'icontains'))

    def test_create_filter_input_subtype(self) -> None:
        """Test the `create_filter_input_subtype` function."""
        input_object_type = create_filter_input_subtype(
            self.task_filter_trees_roots[1],
            TaskFilter,
            'Task',
        )
        self.assertEqual('TaskUserFilterInputType', input_object_type.__name__)
        self.assertTrue(hasattr(input_object_type, 'last_name'))
        self.assertTrue(hasattr(input_object_type, 'email'))

    def test_create_filter_input_type(self) -> None:
        """Test the `create_filter_input_type` function."""
        input_object_type = create_filter_input_type(
            self.task_filter_trees_roots,
            TaskFilter,
            'Task',
        )
        self.assertEqual('TaskFilterInputType', input_object_type.__name__)
        self.assertTrue(hasattr(input_object_type, 'name'))
        self.assertTrue(hasattr(input_object_type, 'user'))
