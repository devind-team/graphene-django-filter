"""`filter_set` module tests."""

from datetime import datetime, timedelta
from unittest.mock import patch

import graphene
from django.db.models.constants import LOOKUP_SEP
from django.test import TestCase
from graphene_django_filter.filter_set import tree_input_type_to_data

from .filter_sets import TaskFilter


class TreeArgsToDataTest(TestCase):
    """`tree_input_type_to_data` function tests."""

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
        email = graphene.InputField(lambda: TreeArgsToDataTest.TaskUserEmailFilterInputType)
        last_name = graphene.InputField(lambda: TreeArgsToDataTest.TaskUserLastNameFilterInputType)

    class TaskCreatedAtInputType(graphene.InputObjectType):
        gt = graphene.DateTime()

    class TaskCompletedAtInputType(graphene.InputObjectType):
        lg = graphene.DateTime()

    TaskFilterInputType = type(
        'TaskFilterInputType',
        (graphene.InputObjectType,),
        {
            'name': graphene.InputField(
                lambda: TreeArgsToDataTest.TaskNameFilterInputType,
            ),
            'description': graphene.InputField(
                lambda: TreeArgsToDataTest.TaskDescriptionFilterInputType,
            ),
            'user': graphene.InputField(
                lambda: TreeArgsToDataTest.TaskUserFilterInputType,
            ),
            'created_at': graphene.InputField(
                lambda: TreeArgsToDataTest.TaskCreatedAtInputType,
            ),
            'completed_at': graphene.InputField(
                lambda: TreeArgsToDataTest.TaskCompletedAtInputType,
            ),
            'or': graphene.InputField(
                lambda: TreeArgsToDataTest.TaskFilterInputType,
            ),
            'and': graphene.InputField(
                lambda: TreeArgsToDataTest.TaskFilterInputType,
            ),
        },
    )

    def setUp(self) -> None:
        """Set up `tree_input_type_to_data` function tests."""
        self.gt_datetime = datetime.today() - timedelta(days=1)
        self.lt_datetime = datetime.today()
        self.tree_input_type = self.TaskFilterInputType._meta.container({
            'name': self.TaskNameFilterInputType._meta.container({'exact': 'Important task'}),
            'description': self.TaskDescriptionFilterInputType._meta.container(
                {'exact': 'This task in very important'},
            ),
            'user': self.TaskUserFilterInputType._meta.container(
                {'email': self.TaskUserEmailFilterInputType._meta.container({'contains': 'dev'})},
            ),
            'or': self.TaskFilterInputType._meta.container({
                'created_at': self.TaskCreatedAtInputType._meta.container(
                    {'gt': self.gt_datetime},
                ),
            }),
            'and': self.TaskFilterInputType._meta.container({
                'completed_at': self.TaskCompletedAtInputType._meta.container(
                    {'lt': self.lt_datetime},
                ),
            }),
        })

    def test_tree_input_type_to_data(self) -> None:
        """Test the `tree_input_type_to_data` function."""
        data = tree_input_type_to_data(self.tree_input_type)
        self.assertEqual(
            {
                f'name{LOOKUP_SEP}exact': 'Important task',
                f'description{LOOKUP_SEP}exact': 'This task in very important',
                f'user{LOOKUP_SEP}email{LOOKUP_SEP}contains': 'dev',
                'or': {
                    'created_at__gt': self.gt_datetime,
                },
                'and': {
                    'completed_at__lt': self.lt_datetime,
                },
            },
            data,
        )


class AdvancedFilterSetTest(TestCase):
    """`AdvancedFilterSetTest` class tests."""

    def test_get_form_class(self) -> None:
        """Test getting a tree form class with the `get_form_class` method."""
        form_class = TaskFilter().get_form_class()
        self.assertEqual('TaskFilterTreeForm', form_class.__name__)
        form = form_class(or_form=form_class())
        self.assertIsInstance(form.or_form, form_class)
        self.assertIsNone(form.and_form)

    def test_tree_form_errors(self) -> None:
        """Test getting a tree form class errors."""
        form_class = TaskFilter().get_form_class()
        form = form_class(or_form=form_class())
        with patch.object(
            form, 'cleaned_data', new={'name': 'parent_name_data'}, create=True,
        ), patch.object(
            form.or_form, 'cleaned_data', new={'name': 'child_name_data'}, create=True,
        ):
            form.add_error('name', 'parent_form_error')
            form.or_form.add_error('name', 'child_form_error')
            self.assertEqual(
                {
                    'name': ['parent_form_error'],
                    'or': {
                        'name': ['child_form_error'],
                    },
                }, form.errors,
            )
