"""`connection_field` module tests."""

from django.test import TestCase
from django_filters import FilterSet
from graphene_django_filter import AdvancedDjangoFilterConnectionField

from .filtersets import TaskFilter
from .object_types import TaskFilterFieldsType, TaskFilterSetClassType


class AdvancedDjangoFilterConnectionFieldTests(TestCase):
    """The `AdvancedDjangoFilterConnectionField` class tests."""

    def test_init(self) -> None:
        """Test the `__init__` method."""
        AdvancedDjangoFilterConnectionField(TaskFilterFieldsType)
        advanced_django_filter_connection_field = AdvancedDjangoFilterConnectionField(
            TaskFilterFieldsType,
            filter_input_type_prefix='Task',
        )
        self.assertEqual('Task', advanced_django_filter_connection_field.filter_input_type_prefix)
        with self.assertRaisesMessage(
            AssertionError,
            'Use the `AdvancedFilterSet` class with the `AdvancedDjangoFilterConnectionField`',
        ):
            AdvancedDjangoFilterConnectionField(
                TaskFilterFieldsType,
                filterset_class=FilterSet,
                filter_input_type_prefix='Task',
            )
        with self.assertWarnsRegex(
            UserWarning,
            r'The `filterset_class` argument without `filter_input_type_prefix`.+',
        ):
            AdvancedDjangoFilterConnectionField(TaskFilterFieldsType, filterset_class=TaskFilter)
        with self.assertWarnsRegex(
            UserWarning,
            r'The `filterset_class` field of `TaskFilterSetClassType` Meta.+',
        ):
            AdvancedDjangoFilterConnectionField(TaskFilterSetClassType)

    def test_provided_filterset_class(self) -> None:
        """Test the `provided_filterset_class` property."""
        self.assertEqual(
            TaskFilter,
            AdvancedDjangoFilterConnectionField(
                TaskFilterFieldsType,
                filterset_class=TaskFilter,
                filter_input_type_prefix='Task',
            ).provided_filterset_class,
        )
        self.assertEqual(
            TaskFilter,
            AdvancedDjangoFilterConnectionField(
                TaskFilterSetClassType,
                filter_input_type_prefix='Task',
            ).provided_filterset_class,
        )

    def test_filter_input_type_prefix(self) -> None:
        """Test the `filter_input_type_prefix` property."""
        self.assertEqual(
            'Task',
            AdvancedDjangoFilterConnectionField(
                TaskFilterSetClassType,
                filter_input_type_prefix='Task',
            ).filter_input_type_prefix,
        )
        with self.assertWarns(UserWarning):
            self.assertEqual(
                'TaskFilterFieldsTaskFilter',
                AdvancedDjangoFilterConnectionField(
                    TaskFilterFieldsType,
                    filterset_class=TaskFilter,
                ).filter_input_type_prefix,
            )
        self.assertEqual(
            'TaskFilterFields',
            AdvancedDjangoFilterConnectionField(
                TaskFilterFieldsType,
            ).filter_input_type_prefix,
        )

    def test_filtering_args(self) -> None:
        """Test the `filtering_args` property."""
        tasks = AdvancedDjangoFilterConnectionField(
            TaskFilterFieldsType,
            description='Advanced filter field',
        )
        filtering_args = tasks.filtering_args
        self.assertEqual(('filter',), tuple(filtering_args.keys()))
        self.assertEqual(
            'TaskFilterFieldsFilterInputType',
            filtering_args['filter'].type.__name__,
        )
