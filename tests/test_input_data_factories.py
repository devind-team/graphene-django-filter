"""Input data factories tests."""

from collections import OrderedDict
from contextlib import contextmanager
from datetime import datetime, timedelta
from typing import Any, Generator, Tuple, Type, cast
from unittest.mock import MagicMock, patch

import graphene
from django.contrib.postgres.search import (
    SearchQuery,
    SearchRank,
    SearchVector,
    TrigramDistance,
    TrigramSimilarity,
)
from django.core.exceptions import ValidationError
from django.db import models
from django.test import TestCase
from graphene.types.inputobjecttype import InputObjectTypeContainer
from graphene_django_filter.filters import (
    SearchQueryFilter,
    SearchRankFilter,
    TrigramFilter,
)
from graphene_django_filter.filterset import AdvancedFilterSet
from graphene_django_filter.input_data_factories import (
    create_data,
    create_search_config,
    create_search_query,
    create_search_query_data,
    create_search_rank_data,
    create_search_rank_weights,
    create_search_vector,
    create_trigram_data,
    tree_input_type_to_data,
    validate_search_query,
    validate_search_vector_fields,
)
from graphene_django_filter.input_types import (
    FloatLookupsInputType,
    SearchConfigInputType,
    SearchQueryFilterInputType,
    SearchQueryInputType,
    SearchRankFilterInputType,
    SearchRankWeightsInputType,
    SearchVectorInputType,
    SearchVectorWeight,
    TrigramFilterInputType,
    TrigramSearchKind,
)


class InputDataFactoriesTests(TestCase):
    """Input data factories tests."""

    filterset_class_mock = cast(
        Type[AdvancedFilterSet],
        MagicMock(
            get_full_text_search_fields=MagicMock(
                return_value=OrderedDict([
                    ('field1', MagicMock()),
                    ('field2', MagicMock()),
                ]),
            ),
        ),
    )

    rank_weights_input_type = SearchRankWeightsInputType._meta.container({
        'A': 0.9,
        'B': SearchRankWeightsInputType.B.kwargs['default_value'],
        'C': SearchRankWeightsInputType.C.kwargs['default_value'],
        'D': SearchRankWeightsInputType.D.kwargs['default_value'],
    })

    invalid_search_query_input_type = SearchQueryInputType._meta.container({})
    config_search_query_input_type = SearchConfigInputType._meta.container({
        'config': SearchConfigInputType._meta.container({
            'value': 'russian',
            'is_field': False,
        }),
        'value': 'value',
    })
    expressions_search_query_input_type = SearchQueryInputType._meta.container({
        'value': 'value1',
        'and': [
            SearchQueryInputType._meta.container({'value': 'and_value1'}),
            SearchQueryInputType._meta.container({'value': 'and_value2'}),
        ],
        'or': [
            SearchQueryInputType._meta.container({'value': 'or_value1'}),
            SearchQueryInputType._meta.container({'value': 'or_value2'}),
        ],
        'not': SearchQueryInputType._meta.container({'value': 'not_value'}),
    })

    search_rank_input_type = SearchRankFilterInputType._meta.container({
        'vector': MagicMock(),
        'query': MagicMock(),
        'lookups': FloatLookupsInputType._meta.container({'gt': 0.8, 'lt': 0.9}),
        'weights': rank_weights_input_type,
        'cover_density': True,
        'normalization': 2,
    })

    @contextmanager
    def patch_vector_and_query_factories(
        self,
    ) -> Generator[Tuple[MagicMock, MagicMock, MagicMock, MagicMock], Any, None]:
        """Patch `create_search_vector` and `create_search_query` functions."""
        with patch(
            'graphene_django_filter.input_data_factories.create_search_vector',
        ) as create_search_vector_mock, patch(
            'graphene_django_filter.input_data_factories.create_search_query',
        ) as create_search_query_mock:
            search_vector_mock = MagicMock()
            create_search_vector_mock.return_value = search_vector_mock
            search_query_mock = MagicMock()
            create_search_query_mock.return_value = search_query_mock
            yield (
                create_search_vector_mock,
                search_vector_mock,
                create_search_query_mock,
                search_query_mock,
            )

    class TaskNameFilterInputType(graphene.InputObjectType):
        exact = graphene.String()
        trigram = graphene.InputField(TrigramFilterInputType)

    class TaskDescriptionFilterInputType(graphene.InputObjectType):
        exact = graphene.String()

    class TaskUserEmailFilterInputType(graphene.InputObjectType):
        exact = graphene.String()
        iexact = graphene.String()
        contains = graphene.String()
        icontains = graphene.String()

    class TaskUserLastNameFilterInputType(graphene.InputObjectType):
        exact = graphene.String()

    class TaskUserFilterInputType(graphene.InputObjectType):
        exact = graphene.String()
        email = graphene.InputField(
            lambda: InputDataFactoriesTests.TaskUserEmailFilterInputType,
        )
        last_name = graphene.InputField(
            lambda: InputDataFactoriesTests.TaskUserLastNameFilterInputType,
        )

    class TaskCreatedAtInputType(graphene.InputObjectType):
        gt = graphene.DateTime()

    class TaskCompletedAtInputType(graphene.InputObjectType):
        lg = graphene.DateTime()

    TaskFilterInputType = type(
        'TaskFilterInputType',
        (graphene.InputObjectType,),
        {
            'name': graphene.InputField(
                lambda: InputDataFactoriesTests.TaskNameFilterInputType,
            ),
            'description': graphene.InputField(
                lambda: InputDataFactoriesTests.TaskDescriptionFilterInputType,
            ),
            'user': graphene.InputField(
                lambda: InputDataFactoriesTests.TaskUserFilterInputType,
            ),
            'created_at': graphene.InputField(
                lambda: InputDataFactoriesTests.TaskCreatedAtInputType,
            ),
            'completed_at': graphene.InputField(
                lambda: InputDataFactoriesTests.TaskCompletedAtInputType,
            ),
            'and': graphene.InputField(
                graphene.List(lambda: InputDataFactoriesTests.TaskFilterInputType),
            ),
            'or': graphene.InputField(
                graphene.List(lambda: InputDataFactoriesTests.TaskFilterInputType),
            ),
            'not': graphene.InputField(
                lambda: InputDataFactoriesTests.TaskFilterInputType,
            ),
            'search_query': graphene.InputField(
                SearchQueryFilterInputType,
            ),
            'search_rank': graphene.InputField(
                SearchRankFilterInputType,
            ),
        },
    )

    task_filterset_class_mock = cast(
        Type[AdvancedFilterSet],
        MagicMock(
            get_full_text_search_fields=MagicMock(
                return_value=OrderedDict([
                    ('name', MagicMock()),
                ]),
            ),
        ),
    )
    gt_datetime = datetime.today() - timedelta(days=1)
    lt_datetime = datetime.today()
    tree_input_type = TaskFilterInputType._meta.container({
        'name': TaskNameFilterInputType._meta.container({
            'exact': 'Important task',
            'trigram': TrigramFilterInputType._meta.container({
                'kind': TrigramSearchKind.SIMILARITY,
                'lookups': FloatLookupsInputType._meta.container({'gt': 0.8}),
                'value': 'Buy some milk',
            }),
        }),
        'description': TaskDescriptionFilterInputType._meta.container(
            {'exact': 'This task is very important'},
        ),
        'user': TaskUserFilterInputType._meta.container(
            {'email': TaskUserEmailFilterInputType._meta.container({'contains': 'dev'})},
        ),
        'and': [
            TaskFilterInputType._meta.container({
                'completed_at': TaskCompletedAtInputType._meta.container({'lt': lt_datetime}),
            }),
        ],
        'or': [
            TaskFilterInputType._meta.container({
                'created_at': TaskCreatedAtInputType._meta.container({'gt': gt_datetime}),
            }),
        ],
        'not': TaskFilterInputType._meta.container({
            'user': TaskUserFilterInputType._meta.container(
                {'first_name': TaskUserEmailFilterInputType._meta.container({'exact': 'John'})},
            ),
        }),
        'search_query': SearchQueryFilterInputType._meta.container({
            'vector': SearchVectorInputType._meta.container({'fields': ['name']}),
            'query': SearchQueryInputType._meta.container({'value': 'Fix the bug'}),
        }),
        'search_rank': SearchRankFilterInputType._meta.container({
            'vector': SearchVectorInputType._meta.container({'fields': ['name']}),
            'query': SearchQueryInputType._meta.container({'value': 'Fix the bug'}),
            'lookups': FloatLookupsInputType._meta.container({'gt': 0.8}),
            'cover_density': False,
        }),
    })

    def test_validate_search_query(self) -> None:
        """Test the `validate_search_query` function."""
        for key in ('value', 'and', 'or', 'not'):
            search_query_input_type = SearchQueryInputType._meta.container({
                key: 'value',
            })
            validate_search_query(search_query_input_type)
        with self.assertRaisesMessage(
            ValidationError,
            'The search query must contains at least one required field '
            'such as `value`, `and`, `or`, `not`.',
        ):
            validate_search_query(SearchQueryInputType._meta.container({}))

    def test_validate_search_vector_fields(self) -> None:
        """Test the `validate_search_vector_fields` function."""
        validate_search_vector_fields(self.filterset_class_mock, ['field1', 'field2'])
        with self.assertRaisesMessage(
            ValidationError,
            'The `field3` field is not included in full text search fields',
        ):
            validate_search_vector_fields(self.filterset_class_mock, ['field1', 'field2', 'field3'])

    def test_create_search_rank_weights(self) -> None:
        """Test the `create_search_rank_weights` function."""
        self.assertEqual(
            [0.1, 0.2, 0.4, 0.9],
            create_search_rank_weights(self.rank_weights_input_type),
        )

    def test_create_search_config(self) -> None:
        """Test the `create_search_config` function."""
        string_input_type = SearchConfigInputType._meta.container({
            'value': 'russian',
            'is_field': False,
        })
        string_config = create_search_config(string_input_type)
        self.assertEqual(string_input_type.value, string_config)
        field_input_type = SearchConfigInputType._meta.container({
            'value': 'russian',
            'is_field': True,
        })
        field_config = create_search_config(field_input_type)
        self.assertEqual(models.F('russian'), field_config)

    def test_create_search_query(self) -> None:
        """Test the `create_search_query` function."""
        with self.assertRaises(ValidationError):
            create_search_query(self.invalid_search_query_input_type)
        config_search_query = create_search_query(self.config_search_query_input_type)
        self.assertEqual(SearchQuery('value', config='russian'), config_search_query)
        expressions_search_query = create_search_query(self.expressions_search_query_input_type)
        self.assertEqual(
            SearchQuery('value1') & (
                SearchQuery('and_value1') & SearchQuery('and_value2')
            ) & (
                SearchQuery('or_value1') | SearchQuery('or_value2')
            ) & ~SearchQuery('not_value'),
            expressions_search_query,
        )

    def test_create_search_vector(self) -> None:
        """Test the `create_search_vector` function."""
        invalid_input_type = SearchVectorInputType._meta.container({
            'fields': ['field1', 'field2', 'field3'],
        })
        with self.assertRaises(ValidationError):
            create_search_vector(invalid_input_type, self.filterset_class_mock)
        config_input_type = SearchVectorInputType._meta.container({
            'fields': ['field1', 'field2'],
            'config': SearchConfigInputType._meta.container({
                'value': 'russian',
            }),
        })
        config_search_vector = create_search_vector(config_input_type, self.filterset_class_mock)
        self.assertEqual(SearchVector('field1', 'field2', config='russian'), config_search_vector)
        weight_input_type = SearchVectorInputType._meta.container({
            'fields': ['field1', 'field2'],
            'weight': SearchVectorWeight.A,
        })
        weight_search_vector = create_search_vector(weight_input_type, self.filterset_class_mock)
        self.assertEqual(SearchVector('field1', 'field2', weight='A'), weight_search_vector)

    def test_create_trigram_data(self) -> None:
        """Test the `create_trigram_data` function."""
        for trigram_class in (TrigramSimilarity, TrigramDistance):
            with self.subTest(trigram_class=trigram_class):
                similarity_input_type = TrigramFilterInputType._meta.container({
                    'kind': TrigramSearchKind.SIMILARITY
                    if trigram_class == TrigramSimilarity else TrigramSearchKind.DISTANCE,
                    'lookups': FloatLookupsInputType._meta.container({'gt': 0.8, 'lt': 0.9}),
                    'value': 'value',
                })
                trigram_data = create_trigram_data(similarity_input_type, 'field__trigram')
                expected_trigram_data = {
                    'field__trigram__gt': TrigramFilter.Value(
                        annotation_value=trigram_class('field', 'value'),
                        search_value=0.8,
                    ),
                    'field__trigram__lt': TrigramFilter.Value(
                        annotation_value=trigram_class('field', 'value'),
                        search_value=0.9,
                    ),
                }
                self.assertEqual(expected_trigram_data, trigram_data)

    @patch.object(
        SearchRank,
        '__eq__',
        new=lambda self, other: str(self) + self.function == str(other) + other.function,
    )
    def test_create_search_rank_data(self) -> None:
        """Test the `create_search_rank_data` function."""
        with self.patch_vector_and_query_factories() as mocks:
            create_sv_mock, sv_mock, create_sq_mock, sq_mock = mocks
            search_rank_data = create_search_rank_data(
                self.search_rank_input_type,
                'field',
                self.filterset_class_mock,
            )
            expected_search_rank = SearchRank(
                vector=sv_mock,
                query=sq_mock,
                weights=[0.1, 0.2, 0.4, 0.9],
                cover_density=True,
                normalization=2,
            )
            self.assertEqual(
                {
                    'field__gt': SearchRankFilter.Value(
                        annotation_value=expected_search_rank,
                        search_value=0.8,
                    ),
                    'field__lt': SearchRankFilter.Value(
                        annotation_value=expected_search_rank,
                        search_value=0.9,
                    ),
                }, search_rank_data,
            )
            create_sv_mock.assert_called_with(
                self.search_rank_input_type.vector,
                self.filterset_class_mock,
            )
            create_sq_mock.assert_called_with(self.search_rank_input_type.query)

    def test_create_search_query_data(self) -> None:
        """Test the `create_search_query_data` function."""
        with self.patch_vector_and_query_factories() as mocks:
            create_sv_mock, sv_mock, create_sq_mock, sq_mock = mocks
            vector = MagicMock()
            query = MagicMock()
            search_query_data = create_search_query_data(
                SearchQueryFilterInputType._meta.container({
                    'vector': vector,
                    'query': query,
                }),
                'field',
                self.filterset_class_mock,
            )
            self.assertEqual(
                {
                    'field': SearchQueryFilter.Value(
                        annotation_value=sv_mock,
                        search_value=sq_mock,
                    ),
                }, search_query_data,
            )
            create_sv_mock.assert_called_once_with(vector, self.filterset_class_mock)
            create_sq_mock.assert_called_once_with(query)

    def test_create_data(self) -> None:
        """Test the `create_data` function."""
        with patch(
            'graphene_django_filter.input_data_factories.DATA_FACTORIES',
            new={
                'search_query': MagicMock(return_value=MagicMock()),
                'search_rank': MagicMock(return_value=MagicMock()),
                'trigram': MagicMock(return_value=MagicMock()),
            },
        ):
            from graphene_django_filter.input_data_factories import DATA_FACTORIES
            for factory_key, factory in DATA_FACTORIES.items():
                value = MagicMock()
                self.assertEqual(
                    factory.return_value,
                    create_data(factory_key, value, self.filterset_class_mock),
                )
                factory.assert_called_once_with(value, factory_key, self.filterset_class_mock)
        with patch('graphene_django_filter.input_data_factories.tree_input_type_to_data') as mock:
            key = 'field'
            value = MagicMock(spec=InputObjectTypeContainer)
            mock.return_value = {key: value}
            self.assertEqual(mock.return_value, create_data(key, value, self.filterset_class_mock))
        key = 'field'
        value = MagicMock()
        self.assertEqual({key: value}, create_data(key, value, self.filterset_class_mock))

    def test_tree_input_type_to_data(self) -> None:
        """Test the `tree_input_type_to_data` function."""
        data = tree_input_type_to_data(self.task_filterset_class_mock, self.tree_input_type)
        expected_data = {
            'name': 'Important task',
            'name__trigram__gt': TrigramFilter.Value(
                annotation_value=TrigramSimilarity('name', 'Buy some milk'),
                search_value=0.8,
            ),
            'description': 'This task is very important',
            'user__email__contains': 'dev',
            'and': [{
                'completed_at__lt': self.lt_datetime,
            }],
            'or': [{
                'created_at__gt': self.gt_datetime,
            }],
            'not': {
                'user__first_name': 'John',
            },
            'search_query': SearchQueryFilter.Value(
                annotation_value=SearchVector('name'),
                search_value=SearchQuery('Fix the bug'),
            ),
            'search_rank__gt': SearchRankFilter.Value(
                annotation_value=SearchRank(
                    vector=SearchVector('name'),
                    query=SearchQuery('Fix the bug'),
                ),
                search_value=0.8,
            ),
        }
        self.assertEqual(expected_data, data)
