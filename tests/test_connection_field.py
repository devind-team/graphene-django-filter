"""`connection_field` module tests."""

from datetime import datetime
from typing import List

from django.test import TestCase
from django.utils.timezone import make_aware
from django_filters import FilterSet
from graphene_django_filter import AdvancedDjangoFilterConnectionField
from graphql.execution import ExecutionResult
from graphql_relay import from_global_id

from .data_generation import generate_data
from .filtersets import TaskFilter
from .object_types import TaskFilterSetClassType
from .schema import schema


class AdvancedDjangoFilterConnectionFieldTest(TestCase):
    """`AdvancedDjangoFilterConnectionField` class tests."""

    users_query = """
    {
        %s(
            filter: {
                isActive: {exact: true}
                or: [
                    {email: {contains: "kate"}}
                    {firstName: {exact: "Jane"}}
                ]
            }
        ) {
            edges {
                node {
                    id
                }
            }
        }
    }
    """
    users_fields_query = users_query % 'usersFields'
    users_filterset_query = users_query % 'usersFilterset'
    tasks_query = f"""
    {{
        %s(
            filter: {{
                completedAt: {{
                    lt: "{make_aware(datetime.strptime('02/02/2021', '%m/%d/%Y')).isoformat()}"
                }}
                createdAt: {{
                    gt: "{make_aware(datetime.strptime('12/31/2019', '%m/%d/%Y')).isoformat()}"
                }}
                or: [
                    {{name: {{contains: "Important"}}}}
                    {{description: {{contains: "important"}}}}
                ]
            }}
        ) {{
            edges {{
                node {{
                    id
                }}
            }}
        }}
    }}
    """
    tasks_fields_query = tasks_query % 'tasksFields'
    tasks_filterset_query = tasks_query % 'tasksFilterset'
    task_groups_query = """
    {
        %s(
            filter: {
                or: [
                    {name: {exact: "Task group №1"}}
                    {
                        and: [
                            {priority: {gte: 5}}
                            {priority: {lte: 10}}
                        ]
                    }
                ]
            }
        ) {
            edges {
                node {
                    id
                }
            }
        }
    }
    """
    task_groups_fields_query = task_groups_query % 'taskGroupsFields'
    task_groups_filterset_query = task_groups_query % 'taskGroupsFilterset'

    @classmethod
    def setUpClass(cls) -> None:
        """`AdvancedDjangoFilterConnectionField` class tests."""
        super().setUpClass()
        generate_data()

    @staticmethod
    def get_ids(execution_result: ExecutionResult, key: str) -> List[int]:
        """Return identifiers from an execution result using a key."""
        return [
            int(from_global_id(edge['node']['id'])[1]) for edge
            in execution_result.data[key]['edges']
        ]

    def test_init(self) -> None:
        """Test the `__init__` method."""
        AdvancedDjangoFilterConnectionField(TaskFilterSetClassType)
        AdvancedDjangoFilterConnectionField(TaskFilterSetClassType, filterset_class=TaskFilter)
        self.assertRaisesMessage(
            lambda: AdvancedDjangoFilterConnectionField(
                TaskFilterSetClassType,
                filterset_class=FilterSet,
            ), 'Use the `AdvancedFilterSet` class with the `AdvancedDjangoFilterConnectionField`',
        )

    def test_filtering_args(self) -> None:
        """Test the `filtering_args` property."""
        tasks = AdvancedDjangoFilterConnectionField(
            TaskFilterSetClassType,
            description='Advanced filter field',
        )
        filtering_args = tasks.filtering_args
        self.assertEqual(('filter',), tuple(filtering_args.keys()))
        self.assertEqual(
            'TaskFilterSetClassFilterInputType',
            filtering_args['filter'].type.__name__,
        )

    def test_users_execution(self) -> None:
        """Test the schema execution by querying users."""
        expected = list(range(16, 51))
        execution_result = schema.execute(self.users_fields_query)
        self.assertEqual(expected, self.get_ids(execution_result, 'usersFields'))
        execution_result = schema.execute(self.users_filterset_query)
        self.assertEqual(expected, self.get_ids(execution_result, 'usersFilterset'))

    def test_tasks_execution(self) -> None:
        """Test the schema execution by querying tasks."""
        expected = list(range(16, 76))
        execution_result = schema.execute(self.tasks_fields_query)
        self.assertEqual(expected, self.get_ids(execution_result, 'tasksFields'))
        execution_result = schema.execute(self.tasks_filterset_query)
        self.assertEqual(expected, self.get_ids(execution_result, 'tasksFilterset'))

    def test_task_groups_execution(self) -> None:
        """Test the schema execution by querying task groups."""
        expected = [1] + list(range(5, 11))
        execution_result = schema.execute(self.task_groups_fields_query)
        self.assertEqual(expected, self.get_ids(execution_result, 'taskGroupsFields'))
        execution_result = schema.execute(self.task_groups_filterset_query)
        self.assertEqual(expected, self.get_ids(execution_result, 'taskGroupsFilterset'))
