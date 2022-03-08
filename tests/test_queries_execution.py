"""Queries execution tests."""

from datetime import datetime
from typing import List

from django.test import TestCase
from django.utils.timezone import make_aware
from graphql.execution import ExecutionResult
from graphql_relay import from_global_id

from .data_generation import generate_data
from .schema import schema


class QueriesExecutionTests(TestCase):
    """Queries execution tests."""

    @classmethod
    def setUpClass(cls) -> None:
        """Set up `QueriesExecutionTests` class."""
        super().setUpClass()
        generate_data()

    def assert_query_execution(self, expected: List[int], query: str, key: str) -> None:
        """Fail if a query execution returns the invalid entries."""
        execution_result = schema.execute(query)
        self.assertEqual(expected, self.get_ids(execution_result, key))

    @staticmethod
    def get_ids(execution_result: ExecutionResult, key: str) -> List[int]:
        """Return identifiers from an execution result using a key."""
        return sorted(
            int(from_global_id(edge['node']['id'])[1]) for edge
            in execution_result.data[key]['edges']
        )


class EdgeCaseTests(QueriesExecutionTests):
    """Tests for executing queries in edge cases."""

    without_filter_query = """
        {
            %s {
                edges {
                    node {
                        id
                    }
                }
            }
        }
    """
    without_filter_fields_query = without_filter_query % 'usersFields'
    without_filter_filterset_query = without_filter_query % 'usersFilterset'
    with_empty_filter_query = """
        {
            %s(filter: {}) {
                edges {
                    node {
                        id
                    }
                }
            }
        }
    """
    with_empty_filter_fields_query = with_empty_filter_query % 'usersFields'
    with_empty_filter_filterset_query = with_empty_filter_query % 'usersFilterset'

    def test_without_filter(self) -> None:
        """Test the schema execution without a filter."""
        expected = list(range(1, 76))
        self.assert_query_execution(expected, self.without_filter_fields_query, 'usersFields')
        self.assert_query_execution(expected, self.without_filter_filterset_query, 'usersFilterset')

    def test_with_empty_filter(self) -> None:
        """Test the schema execution with an empty filter."""
        expected = list(range(1, 76))
        self.assert_query_execution(expected, self.with_empty_filter_fields_query, 'usersFields')
        self.assert_query_execution(
            expected,
            self.with_empty_filter_filterset_query,
            'usersFilterset',
        )


class LogicalExpressionsTests(QueriesExecutionTests):
    """Tests for executing queries with logical expressions."""

    users_query = """
        {
            %s(
                filter: {
                    isActive: {exact: true}
                    or: [
                        {email: {contains: "alice"}}
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
                    and: [
                        {not: {priority: {exact: 7}}}
                        {not: {priority: {exact: 9}}}
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

    def test_users_execution(self) -> None:
        """Test the schema execution by querying users."""
        expected = list(range(16, 51))
        self.assert_query_execution(expected, self.users_fields_query, 'usersFields')
        self.assert_query_execution(expected, self.users_filterset_query, 'usersFilterset')

    def test_tasks_execution(self) -> None:
        """Test the schema execution by querying tasks."""
        expected = list(range(16, 76))
        self.assert_query_execution(expected, self.tasks_fields_query, 'tasksFields')
        self.assert_query_execution(expected, self.tasks_filterset_query, 'tasksFilterset')

    def test_task_groups_execution(self) -> None:
        """Test the schema execution by querying task groups."""
        expected = [1, 5, 6, 8, 10]
        self.assert_query_execution(expected, self.task_groups_fields_query, 'taskGroupsFields')
        self.assert_query_execution(
            expected,
            self.task_groups_filterset_query,
            'taskGroupsFilterset',
        )


class FullTextSearchTests(QueriesExecutionTests):
    """Tests for executing queries with full text search."""

    search_query_query = """
        {
            %s(
                filter: {
                    searchQuery: {
                        vector: {
                            fields: ["first_name"]
                        }
                        query: {
                            or: [
                                {value: "Bob"}
                                {value: "Alice"}
                            ]
                        }
                    }
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
    search_query_fields_query = search_query_query % 'usersFields'
    search_query_filterset_query = search_query_query % 'usersFilterset'
    search_rank_query = """
        {
            %s(
                filter: {
                    searchRank: {
                        vector: {fields: ["name"]}
                        query: {value: "Important task №"}
                        lookups: {gte: 0.08}
                    }
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
    search_rank_fields_query = search_rank_query % 'tasksFields'
    search_rank_filterset_query = search_rank_query % 'tasksFilterset'
    trigram_query = """
        {
            %s(
                filter: {
                    or: [
                        {
                            firstName: {
                                trigram: {
                                    value: "john"
                                    lookups: {gte: 0.85}
                                }
                            }
                        }
                        {
                            lastName: {
                                trigram: {
                                    value: "dou"
                                    lookups: {gte: 0.85}
                                }
                            }
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
    trigram_fields_query = trigram_query % 'usersFields'
    trigram_filterset_query = trigram_query % 'usersFilterset'

    def test_search_query_execution(self) -> None:
        """Test the schema execution by a search query."""
        expected = list(range(1, 31))
        self.assert_query_execution(expected, self.search_query_fields_query, 'usersFields')
        self.assert_query_execution(expected, self.search_query_filterset_query, 'usersFilterset')

    def test_search_rank_execution(self) -> None:
        """Test the schema execution by a search rank."""
        expected = list(range(31, 76))
        self.assert_query_execution(expected, self.search_rank_fields_query, 'tasksFields')
        self.assert_query_execution(expected, self.search_rank_filterset_query, 'tasksFilterset')

    def test_trigram_execution(self) -> None:
        """Test the schema execution by a trigram."""
        expected = list(range(31, 76))
        self.assert_query_execution(expected, self.trigram_fields_query, 'usersFields')
        self.assert_query_execution(expected, self.trigram_filterset_query, 'usersFilterset')
