"""`filterset` module tests."""

from contextlib import ExitStack
from datetime import datetime, timedelta
from unittest.mock import patch

import django_filters
import graphene
from django.db.models.constants import LOOKUP_SEP
from django.test import TestCase
from django.utils.timezone import make_aware
from graphene_django_filter.filterset import AdvancedFilterSet, tree_input_type_to_data

from .data_generation import generate_data
from .filtersets import TaskFilter
from .models import User


class GlobalFunctionsTest(TestCase):
    """Testing global functions of the filterset module."""

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
            lambda: GlobalFunctionsTest.TaskUserEmailFilterInputType,
        )
        last_name = graphene.InputField(
            lambda: GlobalFunctionsTest.TaskUserLastNameFilterInputType,
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
                lambda: GlobalFunctionsTest.TaskNameFilterInputType,
            ),
            'description': graphene.InputField(
                lambda: GlobalFunctionsTest.TaskDescriptionFilterInputType,
            ),
            'user': graphene.InputField(
                lambda: GlobalFunctionsTest.TaskUserFilterInputType,
            ),
            'created_at': graphene.InputField(
                lambda: GlobalFunctionsTest.TaskCreatedAtInputType,
            ),
            'completed_at': graphene.InputField(
                lambda: GlobalFunctionsTest.TaskCompletedAtInputType,
            ),
            'and': graphene.InputField(
                graphene.List(lambda: GlobalFunctionsTest.TaskFilterInputType),
            ),
            'or': graphene.InputField(
                graphene.List(lambda: GlobalFunctionsTest.TaskFilterInputType),
            ),
            'not': graphene.InputField(lambda: GlobalFunctionsTest.TaskFilterInputType),
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
                f'user{LOOKUP_SEP}email{LOOKUP_SEP}contains': 'dev',
                'and': [{
                    'completed_at__lt': self.lt_datetime,
                }],
                'or': [{
                    'created_at__gt': self.gt_datetime,
                }],
                'not': {
                    f'user{LOOKUP_SEP}first_name': 'John',
                },
            },
            data,
        )


class AdvancedFilterSetTest(TestCase):
    """`AdvancedFilterSetTest` class tests."""

    class FindFilterFilterSet(AdvancedFilterSet):
        in_last_name = django_filters.CharFilter(field_name='last_name', lookup_expr='contains')

        class Meta:
            model = User
            fields = {
                'email': ('exact',),
                'first_name': ('iexact',),
            }

    task_filter_data = {
        'user__in': '2,3',
        'and': [
            {'created_at__gt': make_aware(datetime.strptime('12/31/2019', '%m/%d/%Y'))},
            {'completed_at__lt': make_aware(datetime.strptime('02/02/2021', '%m/%d/%Y'))},
        ],
        'or': [
            {'name__contains': 'Important'},
            {'description__contains': 'important'},
        ],
        'not': {
            'user': 2,
        },
    }

    @classmethod
    def setUpClass(cls) -> None:
        """`AdvancedFilterSetTest` class tests."""
        super().setUpClass()
        generate_data()

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
        filterset = AdvancedFilterSetTest.FindFilterFilterSet()
        email_filter = filterset.find_filter('email')
        self.assertEqual(email_filter.field_name, 'email')
        self.assertEqual(email_filter.lookup_expr, 'exact')
        email_filter = filterset.find_filter(f'email{LOOKUP_SEP}exact')
        self.assertEqual(email_filter.field_name, 'email')
        self.assertEqual(email_filter.lookup_expr, 'exact')
        first_name_filter = filterset.find_filter(f'first_name{LOOKUP_SEP}iexact')
        self.assertEqual(first_name_filter.field_name, 'first_name')
        self.assertEqual(first_name_filter.lookup_expr, 'iexact')
        last_name_filter = filterset.find_filter(f'last_name{LOOKUP_SEP}contains')
        self.assertEqual(last_name_filter.field_name, 'last_name')
        self.assertEqual(last_name_filter.lookup_expr, 'contains')

    def test_filter_queryset(self) -> None:
        """Test the `filter_queryset` method."""
        task_filter = TaskFilter(data=self.task_filter_data)
        getattr(task_filter.form, 'errors')  # Ensure form validation before filtering
        tasks = task_filter.filter_queryset(task_filter.queryset.all())
        print(tasks.query)
        self.assertRegex(str(tasks.query), r'\(.+AND.+AND.+AND.+\(.+OR.+\)\)')
        self.assertEqual(60, tasks.count())
