"""FilterSet classes."""

import django_filters

from .models import Task, User


class UserFilter(django_filters.FilterSet):
    """User FilterSet class for testing."""

    class Meta:
        model = User
        fields = (
            'first_name',
            'last_name',
            'sir_name',
            'email',
            'is_active',
            'birthday',
        )


class TaskFilter(django_filters.FilterSet):
    """Task FilterSet class for testing."""

    user__email__iexact = django_filters.CharFilter(field_name='user__email', lookup_expr='iexact')
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
            'user__last_name',
        )
