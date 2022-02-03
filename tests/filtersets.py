"""FilterSet classes."""

import django_filters
from graphene_django_filter import AdvancedFilterSet

from .models import Task, TaskGroup, User


class UserFilter(AdvancedFilterSet):
    """User FilterSet class for testing."""

    first_name__startswith = django_filters.CharFilter(
        field_name='first_name',
        lookup_expr='startswith',
    )
    last_name__contains = django_filters.CharFilter(
        field_name='last_name',
        lookup_expr='contains',
    )
    birthday__range = django_filters.DateFromToRangeFilter(field_name='birthday')

    class Meta:
        model = User
        fields = (
            'first_name',
            'last_name',
            'email',
            'is_active',
            'birthday',
        )


class TaskFilter(AdvancedFilterSet):
    """Task FilterSet class for testing."""

    created_at__gt = django_filters.DateFilter(
        field_name='created_at',
        lookup_expr='gt',
    )
    completed_at__lt = django_filters.DateFilter(
        field_name='completed_at',
        lookup_expr='lt',
    )
    user__email__iexact = django_filters.CharFilter(
        field_name='user__email',
        lookup_expr='iexact',
    )
    user__email__contains = django_filters.CharFilter(
        field_name='user__email',
        lookup_expr='contains',
    )
    user__email__icontains = django_filters.CharFilter(
        field_name='user__email',
        lookup_expr='icontains',
    )

    class Meta:
        model = Task
        fields = (
            'name',
            'description',
            'user',
            'user__email',
            'user__last_name',
        )


class TaskGroupFilter(AdvancedFilterSet):
    """TaskGroup FilterSet class for testing."""

    name__contains = django_filters.CharFilter(
        field_name='name',
        lookup_expr='contains',
    )
    priority_gte = django_filters.NumberFilter(
        field_name='priority',
        lookup_expr='gte',
    )

    class Meta:
        model = TaskGroup
        fields = (
            'name',
            'priority',
            'tasks',
        )
