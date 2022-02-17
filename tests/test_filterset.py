"""`filterset` module tests."""

from collections import OrderedDict
from contextlib import ExitStack
from datetime import datetime, timedelta
from typing import List
from unittest.mock import MagicMock, patch

import graphene
from django.db import models
from django.test import TestCase
from django.utils.timezone import make_aware
from django_filters import CharFilter, Filter
from graphene_django_filter.filters import SearchQueryFilter, SearchRankFilter, TrigramFilter
from graphene_django_filter.filterset import (
    AdvancedFilterSet,
    QuerySetProxy,
    get_q,
    is_full_text_search_lookup_expr,
    is_regular_lookup_expr,
    tree_input_type_to_data,
)

from .data_generation import generate_data
from .filtersets import TaskFilter
from .models import Task, User


class UtilsTests(TestCase):
    """Tests for utility functions and classes of the `filterset` module."""

    class TaskNameFilterInputType(graphene.InputObjectType):
        exact = graphene.String()

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
            lambda: UtilsTests.TaskUserEmailFilterInputType,
        )
        last_name = graphene.InputField(
            lambda: UtilsTests.TaskUserLastNameFilterInputType,
        )

    class TaskCreatedAtInputType(graphene.InputObjectType):
        gt = graphene.DateTime()

    class TaskCompletedAtInputType(graphene.InputObjectType):
        lg = graphene.DateTime()

    TaskFilterInputType = type(
        'TaskFilterInputType',
        (graphene.InputObjectType,),
        {
            'name': graphene.InputField(lambda: UtilsTests.TaskNameFilterInputType),
            'description': graphene.InputField(lambda: UtilsTests.TaskDescriptionFilterInputType),
            'user': graphene.InputField(lambda: UtilsTests.TaskUserFilterInputType),
            'created_at': graphene.InputField(lambda: UtilsTests.TaskCreatedAtInputType),
            'completed_at': graphene.InputField(lambda: UtilsTests.TaskCompletedAtInputType),
            'and': graphene.InputField(graphene.List(lambda: UtilsTests.TaskFilterInputType)),
            'or': graphene.InputField(graphene.List(lambda: UtilsTests.TaskFilterInputType)),
            'not': graphene.InputField(lambda: UtilsTests.TaskFilterInputType),
        },
    )

    gt_datetime = datetime.today() - timedelta(days=1)
    lt_datetime = datetime.today()
    tree_input_type = TaskFilterInputType._meta.container({
        'name': TaskNameFilterInputType._meta.container({'exact': 'Important task'}),
        'description': TaskDescriptionFilterInputType._meta.container(
            {'exact': 'This task in very important'},
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
    })

    def test_tree_input_type_to_data(self) -> None:
        """Test the `tree_input_type_to_data` function."""
        data = tree_input_type_to_data(self.tree_input_type)
        self.assertEqual(
            {
                'name': 'Important task',
                'description': 'This task in very important',
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
            },
            data,
        )

    def test_queryset_proxy(self) -> None:
        """Test the `QuerySetProxy` class."""
        queryset = User.objects.all()
        queryset_proxy = QuerySetProxy(queryset)
        self.assertEqual(queryset.get, queryset_proxy.get)
        self.assertNotEqual(queryset.filter, queryset_proxy.filter)
        self.assertNotEqual(queryset.exclude, queryset_proxy.exclude)
        queryset_proxy.filter(email__contains='kate').exclude(
            models.Q(first_name='John') & models.Q(last_name='Dou'),
        )
        self.assertEqual(
            models.Q(email__contains='kate') & ~(
                models.Q(first_name='John') & models.Q(last_name='Dou')
            ),
            queryset_proxy.q,
        )

    def test_get_q(self) -> None:
        """Test the `test_get_q` function."""
        queryset = User.objects.all()
        filter_obj = Filter(field_name='first_name', lookup_expr='exact')
        q = get_q(queryset, filter_obj, 'John')
        self.assertEqual(models.Q(first_name__exact='John'), q)

    def test_is_full_text_search_lookup(self) -> None:
        """Test the `is_full_text_search_lookup` function."""
        self.assertFalse(is_full_text_search_lookup_expr('name__exact'))
        self.assertTrue(is_full_text_search_lookup_expr('name__full_text_search'))

    def test_is_regular_lookup(self) -> None:
        """Test the `is_regular_lookup` function."""
        self.assertTrue(is_regular_lookup_expr('name__exact'))
        self.assertFalse(is_regular_lookup_expr('name__full_text_search'))


class AdvancedFilterSetTests(TestCase):
    """`AdvancedFilterSetTest` class tests."""

    class FindFilterFilterSet(AdvancedFilterSet):
        in_last_name = CharFilter(field_name='last_name', lookup_expr='contains')

        class Meta:
            model = User
            fields = {
                'email': ('exact',),
                'first_name': ('iexact',),
            }

    gt_datetime = make_aware(datetime.strptime('12/31/2019', '%m/%d/%Y'))
    lt_datetime = make_aware(datetime.strptime('02/02/2021', '%m/%d/%Y'))
    task_filter_data = {
        'user__in': '2,3',
        'and': [
            {'created_at__gt': gt_datetime},
            {'completed_at__lt': lt_datetime},
        ],
        'or': [
            {'name__contains': 'Important'},
            {'description__contains': 'important'},
        ],
        'not': {
            'user': 2,
        },
    }

    class FullTextSearchFilterSet(AdvancedFilterSet):
        class Meta:
            model = Task
            fields = {
                'user__email': ('exact', 'contains'),
                'user__first_name': ('exact', 'contains', 'full_text_search'),
                'user__last_name': ('full_text_search',),
            }

    expected_regular_filters = [
        ('user__email', CharFilter(field_name='user__email', lookup_expr='exact')),
        ('user__email__contains', CharFilter(field_name='user__email', lookup_expr='contains')),
        ('user__first_name', CharFilter(field_name='user__first_name', lookup_expr='exact')),
        (
            'user__first_name__contains',
            CharFilter(field_name='user__first_name', lookup_expr='contains'),
        ),
    ]
    expected_search_query_filters = [
        ('search_query', SearchQueryFilter(field_name='search_query', lookup_expr='exact')),
    ]
    expected_search_rank_filters = [
        ('search_rank', SearchRankFilter(field_name='search_rank', lookup_expr='exact')),
        ('search_rank__gt', SearchRankFilter(field_name='search_rank', lookup_expr='gt')),
        ('search_rank__gte', SearchRankFilter(field_name='search_rank', lookup_expr='gte')),
        ('search_rank__lt', SearchRankFilter(field_name='search_rank', lookup_expr='lt')),
        ('search_rank__lte', SearchRankFilter(field_name='search_rank', lookup_expr='lte')),
    ]
    expected_trigram_filters = [
        (
            'user__first_name__trigram',
            TrigramFilter(field_name='user__first_name__trigram', lookup_expr='exact'),
        ),
        (
            'user__first_name__trigram__gt',
            TrigramFilter(field_name='user__first_name__trigram', lookup_expr='gt'),
        ),
        (
            'user__first_name__trigram__gte',
            TrigramFilter(field_name='user__first_name__trigram', lookup_expr='gte'),
        ),
        (
            'user__first_name__trigram__lt',
            TrigramFilter(field_name='user__first_name__trigram', lookup_expr='lt'),
        ),
        (
            'user__first_name__trigram__lte',
            TrigramFilter(field_name='user__first_name__trigram', lookup_expr='lte'),
        ),
        (
            'user__last_name__trigram',
            TrigramFilter(field_name='user__last_name__trigram', lookup_expr='exact'),
        ),
        (
            'user__last_name__trigram__gt',
            TrigramFilter(field_name='user__last_name__trigram', lookup_expr='gt'),
        ),
        (
            'user__last_name__trigram__gte',
            TrigramFilter(field_name='user__last_name__trigram', lookup_expr='gte'),
        ),
        (
            'user__last_name__trigram__lt',
            TrigramFilter(field_name='user__last_name__trigram', lookup_expr='lt'),
        ),
        (
            'user__last_name__trigram__lte',
            TrigramFilter(field_name='user__last_name__trigram', lookup_expr='lte'),
        ),
    ]

    @classmethod
    def setUpClass(cls) -> None:
        """Set up `AdvancedFilterSetTest` class tests."""
        super().setUpClass()
        generate_data()

    def assertFiltersEqual(self, first: List[tuple], second: List[tuple]) -> None:
        """Fail if the two filter lists unequal."""
        self.assertEqual(len(first), len(second))
        for expected, actual in zip(first, second):
            self.assertEqual(expected[0], actual[0])
            self.assertEqual(type(expected[1]), type(actual[1]))
            self.assertEqual(expected[1].field_name, actual[1].field_name)
            self.assertEqual(expected[1].lookup_expr, actual[1].lookup_expr)

    def test_get_form_class(self) -> None:
        """Test getting a tree form class with the `get_form_class` method."""
        form_class = TaskFilter().get_form_class()
        self.assertEqual('TaskFilterTreeForm', form_class.__name__)
        form = form_class(or_forms=[form_class()], not_form=form_class())
        self.assertEqual(0, len(form.and_forms))
        self.assertEqual(1, len(form.or_forms))
        self.assertIsInstance(form.or_forms[0], form_class)
        self.assertIsInstance(form.not_form, form_class)

    def test_tree_form_errors(self) -> None:
        """Test getting a tree form class errors."""
        form_class = TaskFilter().get_form_class()
        form = form_class(or_forms=[form_class()], not_form=form_class())
        with ExitStack() as stack:
            for f in (form, form.or_forms[0], form.not_form):
                stack.enter_context(
                    patch.object(f, 'cleaned_data', new={'name': 'parent_name_data'}, create=True),
                )
            all_errors = {
                'name': ['root_form_error'],
                'or': {
                    'or_0': {
                        'name': ['or_form_error'],
                    },
                },
                'not': {
                    'name': ['not_form_error'],
                },
            }
            self.assertEqual({}, form.errors)
            form.add_error('name', 'root_form_error')
            self.assertEqual(
                {k: v for k, v in all_errors.items() if k == 'name'},
                form.errors,
            )
            form.or_forms[0].add_error('name', 'or_form_error')
            self.assertEqual(
                {k: v for k, v in all_errors.items() if k in ('name', 'or')},
                form.errors,
            )
            form.not_form.add_error('name', 'not_form_error')
            self.assertEqual(all_errors, form.errors)

    def test_form(self) -> None:
        """Test the `form` property."""
        empty_filter = TaskFilter()
        self.assertFalse(empty_filter.form.is_bound)
        task_filter = TaskFilter(data=self.task_filter_data)
        self.assertTrue(task_filter.form.is_bound)
        self.assertEqual(
            {k: v for k, v in self.task_filter_data.items() if k not in ('and', 'or', 'not')},
            task_filter.form.data,
        )
        for key in ('and', 'or'):
            forms = getattr(task_filter.form, f'{key}_forms')
            for data, form in zip(self.task_filter_data[key], forms):
                self.assertEqual(data, form.data)
            for form in forms:
                self.assertEqual(0, len(form.and_forms))
                self.assertEqual(0, len(form.or_forms))
        self.assertEqual(self.task_filter_data['not'], task_filter.form.not_form.data)
        self.assertEqual(0, len(task_filter.form.not_form.and_forms))
        self.assertEqual(0, len(task_filter.form.not_form.or_forms))

    def test_find_filter(self) -> None:
        """Test the `find_filter` method."""
        filterset = AdvancedFilterSetTests.FindFilterFilterSet()
        email_filter = filterset.find_filter('email')
        self.assertEqual(email_filter.field_name, 'email')
        self.assertEqual(email_filter.lookup_expr, 'exact')
        email_filter = filterset.find_filter('email__exact')
        self.assertEqual(email_filter.field_name, 'email')
        self.assertEqual(email_filter.lookup_expr, 'exact')
        first_name_filter = filterset.find_filter('first_name__iexact')
        self.assertEqual(first_name_filter.field_name, 'first_name')
        self.assertEqual(first_name_filter.lookup_expr, 'iexact')
        last_name_filter = filterset.find_filter('last_name__contains')
        self.assertEqual(last_name_filter.field_name, 'last_name')
        self.assertEqual(last_name_filter.lookup_expr, 'contains')

    def test_filter_queryset(self) -> None:
        """Test the `filter_queryset` method."""
        task_filter = TaskFilter(data=self.task_filter_data)
        getattr(task_filter.form, 'errors')  # Ensure form validation before filtering
        tasks = task_filter.filter_queryset(task_filter.queryset.all())
        expected_tasks = Task.objects.filter(
            models.Q(user__in=(2, 3)) & models.Q(created_at__gt=self.gt_datetime) & models.Q(
                completed_at__lt=self.lt_datetime,
            ) & models.Q(
                models.Q(name__contains='Important') | models.Q(description__contains='important'),
            ) & ~models.Q(user=2),
        ).all()
        self.assertEqual(list(expected_tasks), list(tasks))

    def test_get_fields(self) -> None:
        """Test `get_fields` and `get_full_text_search_fields` methods."""
        self.assertEqual(
            OrderedDict([
                ('user__email', ['exact', 'contains']),
                ('user__first_name', ['exact', 'contains']),
            ]),
            self.FullTextSearchFilterSet.get_fields(),
        )
        self.assertEqual(
            OrderedDict([
                ('user__first_name', ['full_text_search']),
                ('user__last_name', ['full_text_search']),
            ]),
            self.FullTextSearchFilterSet.get_full_text_search_fields(),
        )

    def test_create_special_filters_without_field_name(self) -> None:
        """Test the `create_special_filters` method without the `field_name` parameter."""
        base_filters = OrderedDict([('search_rank__gt', MagicMock())])
        filters = AdvancedFilterSet.create_special_filters(base_filters, SearchRankFilter)
        expected_filters = [
            ('search_rank', SearchRankFilter(field_name='search_rank', lookup_expr='exact')),
            ('search_rank__gte', SearchRankFilter(field_name='search_rank', lookup_expr='gte')),
            ('search_rank__lt', SearchRankFilter(field_name='search_rank', lookup_expr='lt')),
            ('search_rank__lte', SearchRankFilter(field_name='search_rank', lookup_expr='lte')),
        ]
        self.assertFiltersEqual(expected_filters, filters.items())

    def test_create_special_filters_with_field_name(self) -> None:
        """Test the `create_special_filters` method with the `field_name` parameter."""
        base_filters = OrderedDict([('name__trigram__gt', MagicMock())])
        filters = AdvancedFilterSet.create_special_filters(base_filters, TrigramFilter, 'name')
        expected_filters = [
            ('name__trigram', TrigramFilter(field_name='name__trigram', lookup_expr='exact')),
            ('name__trigram__gte', TrigramFilter(field_name='name__trigram', lookup_expr='gte')),
            ('name__trigram__lt', TrigramFilter(field_name='name__trigram', lookup_expr='lt')),
            ('name__trigram__lte', TrigramFilter(field_name='name__trigram', lookup_expr='lte')),
        ]
        self.assertFiltersEqual(expected_filters, filters.items())

    @patch.object(
        AdvancedFilterSet,
        'get_full_text_search_fields',
        new=MagicMock(return_value=OrderedDict()),
    )
    def test_create_full_text_search_filters_without_fields(self) -> None:
        """Test the `create_full_text_search_filters` method without full text search fields."""
        base_filters = OrderedDict()
        filters = self.FullTextSearchFilterSet.create_full_text_search_filters(base_filters)
        expected_filters = []
        self.assertFiltersEqual(expected_filters, filters.items())

    @patch(
        'graphene_django_filter.conf.FIXED_SETTINGS', new={
            'IS_POSTGRESQL': False,
            'HAS_TRIGRAM_EXTENSION': False,
        },
    )
    def test_create_full_text_search_filters_without_postgresql(self) -> None:
        """Test the `create_full_text_search_filters` method if the database is not PostgreSQL."""
        base_filters = OrderedDict()
        with self.assertWarns(UserWarning):
            filters = self.FullTextSearchFilterSet.create_full_text_search_filters(base_filters)
        expected_filters = []
        self.assertFiltersEqual(expected_filters, filters.items())

    @patch(
        'graphene_django_filter.conf.FIXED_SETTINGS', new={
            'IS_POSTGRESQL': True,
            'HAS_TRIGRAM_EXTENSION': False,
        },
    )
    def test_create_full_text_search_filters_without_trigrams(self) -> None:
        """Test the `create_full_text_search_filters` method.

        The database has not `pg_trgm` extension.
        """
        base_filters = OrderedDict()
        with self.assertWarns(UserWarning):
            filters = self.FullTextSearchFilterSet.create_full_text_search_filters(base_filters)
        expected_filters = [
            *self.expected_search_query_filters,
            *self.expected_search_rank_filters,
        ]
        self.assertFiltersEqual(expected_filters, filters.items())

    def test_create_full_text_search_filter(self) -> None:
        """Test the `create_full_text_search_filters` method with all filters."""
        base_filters = OrderedDict(
            [('search_query', SearchQueryFilter(field_name='', lookup_expr='exact'))],
        )
        filters = self.FullTextSearchFilterSet.create_full_text_search_filters(base_filters)
        expected_filters = [
            *self.expected_search_rank_filters,
            *self.expected_trigram_filters,
        ]
        self.assertFiltersEqual(expected_filters, filters.items())

    def test_get_filters(self) -> None:
        """Test the `get_filters` method."""
        filters = self.FullTextSearchFilterSet.get_filters()
        expected_filters = [
            *self.expected_regular_filters,
            *self.expected_search_query_filters,
            *self.expected_search_rank_filters,
            *self.expected_trigram_filters,
        ]
        self.assertFiltersEqual(expected_filters, filters.items())
