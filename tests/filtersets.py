"""FilterSet classes."""

from graphene_django_filter import AdvancedFilterSet

from .models import Task, TaskGroup, User


class UserFilter(AdvancedFilterSet):
    """User FilterSet class for testing."""

    class Meta:
        model = User
        fields = {
            'email': ('exact', 'startswith', 'contains'),
            'first_name': ('exact', 'contains'),
            'last_name': ('exact', 'contains'),
            'is_active': ('exact',),
            'birthday': ('exact',),
        }


class TaskFilter(AdvancedFilterSet):
    """Task FilterSet class for testing."""

    class Meta:
        model = Task
        fields = {
            'name': ('exact', 'contains'),
            'created_at': ('gt',),
            'completed_at': ('lt',),
            'description': ('exact', 'contains'),
            'user': ('exact', 'in'),
            'user__email': ('exact', 'iexact', 'contains', 'icontains'),
            'user__last_name': ('exact', 'contains'),
        }


class TaskGroupFilter(AdvancedFilterSet):
    """TaskGroup FilterSet class for testing."""

    class Meta:
        model = TaskGroup
        fields = {
            'name': ('exact', 'contains'),
            'priority': ('exact', 'gte', 'lte'),
            'tasks': ('exact',),
        }
