"""DjangoFilterConnectionField tests."""

from django.test import TestCase
from graphene_django_filter import AdvancedDjangoFilterConnectionField

from .object_types import TaskFilterSetClassType


class AdvancedDjangoFilterConnectionFieldTest(TestCase):
    """AdvancedDjangoFilterConnectionField tests."""

    def test_filtering_args(self) -> None:
        """Test the `filtering_args` property."""
        tasks = AdvancedDjangoFilterConnectionField(
            TaskFilterSetClassType,
            description='Advanced filter field',
        )
        filtering_args = tasks.filtering_args
        self.assertEqual(('filter',), tuple(filtering_args.keys()))
        self.assertEqual(
            'TaskFilterSetClassFilterInputType',
            filtering_args['filter'].type.__name__,
        )
