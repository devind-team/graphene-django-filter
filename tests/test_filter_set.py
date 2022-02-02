"""`filter_set` module tests."""

from datetime import datetime, timedelta

import graphene
from django.db.models.constants import LOOKUP_SEP
from django.test import TestCase
from graphene_django_filter.filter_set import tree_input_type_to_data


class TestTreeArgsToData(TestCase):
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
        email = graphene.InputField(lambda: TestTreeArgsToData.TaskUserEmailFilterInputType)
        last_name = graphene.InputField(lambda: TestTreeArgsToData.TaskUserLastNameFilterInputType)

    class TaskCreatedAtInputType(graphene.InputObjectType):
        gt = graphene.DateTime()

    class TaskCompletedAtInputType(graphene.InputObjectType):
        lg = graphene.DateTime()

    TaskFilterInputType = type(
        'TaskFilterInputType',
        (graphene.InputObjectType,),
        {
            'name': graphene.InputField(
                lambda: TestTreeArgsToData.TaskNameFilterInputType,
            ),
            'description': graphene.InputField(
                lambda: TestTreeArgsToData.TaskDescriptionFilterInputType,
            ),
            'user': graphene.InputField(
                lambda: TestTreeArgsToData.TaskUserFilterInputType,
            ),
            'created_at': graphene.InputField(
                lambda: TestTreeArgsToData.TaskCreatedAtInputType,
            ),
            'completed_at': graphene.InputField(
                lambda: TestTreeArgsToData.TaskCompletedAtInputType,
            ),
            'or': graphene.InputField(
                lambda: TestTreeArgsToData.TaskFilterInputType,
            ),
            'and': graphene.InputField(
                lambda: TestTreeArgsToData.TaskFilterInputType,
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
