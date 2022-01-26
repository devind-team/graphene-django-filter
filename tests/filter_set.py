"""FilterSet classes."""

from django_filters import FilterSet

from .models import Task, User


class UserFilter(FilterSet):
    """User FilterSet class for testing."""

    class Meta:
        model = User
        fields = [
            'first_name',
            'last_name',
            'sir_name',
            'email',
            'is_active',
            'birthday',
        ]


class TaskFilter(FilterSet):
    """Task FilterSet class for testing."""

    class Meta:
        model = Task
        fields = [
            'name',
            'user__email',
            'user__last_name',
        ]
