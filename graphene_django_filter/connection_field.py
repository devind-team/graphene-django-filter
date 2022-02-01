"""`AdvancedDjangoFilterConnectionField` class module.

Use the `AdvancedDjangoFilterConnectionField` class from this
module instead of the `DjangoFilterConnectionField` from graphene-django.
"""

from typing import Any, Dict, Iterable, Optional, Type

import graphene
from django.db import models
from django_filters import FilterSet
from graphene_django import DjangoObjectType
from graphene_django.filter import DjangoFilterConnectionField

from .filter_set import AdvancedFilterSet
from .input_type_factories import get_filtering_args_from_filterset


class AdvancedDjangoFilterConnectionField(DjangoFilterConnectionField):
    """Allow you to use advanced filters provided by this library."""

    def __init__(
        self,
        type: Type[DjangoObjectType],
        fields: Optional[Dict[str, list]] = None,
        order_by: Any = None,
        extra_filter_meta: Optional[dict] = None,
        filterset_class: Optional[Type[AdvancedFilterSet]] = None,
        *args,
        **kwargs
    ) -> None:
        assert filterset_class is None or issubclass(filterset_class, AdvancedFilterSet), \
            'Use the `AdvancedFilterSet` class with the `AdvancedDjangoFilterConnectionField`'
        super().__init__(
            type,
            fields,
            order_by,
            extra_filter_meta,
            filterset_class,
            *args,
            **kwargs
        )

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
