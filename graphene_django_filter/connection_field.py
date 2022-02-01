"""AdvancedDjangoFilterConnectionField module.

Use DjangoFilterConnectionField class from this
module instead of DjangoFilterConnectionField from graphene-django.
"""

from typing import Any, Dict, Iterable, Type

import graphene
from django.db import models
from django_filters import FilterSet
from graphene_django.filter import DjangoFilterConnectionField

from .input_type_builders import get_filtering_args_from_filterset


class AdvancedDjangoFilterConnectionField(DjangoFilterConnectionField):
    """Allow you to use advanced filters provided by this library."""

    @property
    def filtering_args(self) -> dict:
        """Return filtering args from the filterset."""
        if not self._filtering_args:
            self._filtering_args = get_filtering_args_from_filterset(
                self.filterset_class, self.node_type,
            )
        return self._filtering_args

    @classmethod
    def resolve_queryset(
        cls,
        connection: object,
        iterable: Iterable,
        info: graphene.ResolveInfo,
        args: Dict[str, Any],
        filtering_args: Dict[str, graphene.InputField],
        filterset_class: Type[FilterSet],
    ) -> models.QuerySet:
        """Return a filtered QuerySet."""
        return super(DjangoFilterConnectionField, cls).resolve_queryset(
            connection, iterable, info, args,
        )
