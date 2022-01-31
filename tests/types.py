"""Types classes."""

import graphene
from graphene_django import DjangoObjectType

from .filter_set import TaskFilter, UserFilter
from .models import Task, User


class UserFilterFieldsType(DjangoObjectType):
    """UserType with the `filter_fields` field in the Meta class."""

    class Meta:
        model = User
        fields = '__all__'
        filter_fields = {
            'first_name': ('exact',),
            'last_name': ('exact',),
            'sir_name': ('exact',),
            'email': ('exact',),
            'is_active': ('exact',),
            'birthday': ('exact',),
        }


class UserFilterSetClassType(DjangoObjectType):
    """UserType with the `filterset_class` field in the Meta class."""

    class Meta:
        model = User
        fields = '__all__'
        filterset_class = UserFilter


class TaskFilterFieldsType(DjangoObjectType):
    """TaskType with the `filter_fields` field in the Meta class."""

    user = graphene.Field(UserFilterFieldsType, description='User field')

    class Meta:
        model = Task
        fields = ('name', 'user')
        filter_fields = {
            'name': ('exact',),
            'user__email': ('iexact', 'contains', 'icontains'),
        }


class TaskFilterSetClassType(DjangoObjectType):
    """TaskType with the `filterset_class` field in the Meta class."""

    user = graphene.Field(UserFilterSetClassType, description='User field')

    class Meta:
        model = Task
        fields = ('name', 'user')
        filterset_class = TaskFilter
