"""`AdvancedDjangoFilterConnectionField` class module.

Use the `AdvancedDjangoFilterConnectionField` class from this
module instead of the `DjangoFilterConnectionField` from graphene-django.
"""

from typing import Any, Dict, Iterable, Optional, Type

import graphene
from django.core.exceptions import ValidationError
from django.db import models
from graphene_django import DjangoObjectType
from graphene_django.filter import DjangoFilterConnectionField

from .filterset import AdvancedFilterSet
from .filterset_factories import get_filterset_class
from .input_data_factories import tree_input_type_to_data
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
    def filterset_class(self) -> Type[AdvancedFilterSet]:
        """Return a AdvancedFilterSet instead of a FilterSet."""
        if not self._filterset_class:
            fields = self._fields or self.node_type._meta.filter_fields
            meta = {'model': self.model, 'fields': fields}
            if self._extra_filter_meta:
                meta.update(self._extra_filter_meta)
            filterset_class = self._provided_filterset_class or (
                self.node_type._meta.filterset_class
            )
            self._filterset_class = get_filterset_class(filterset_class, **meta)
        return self._filterset_class

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
        filterset_class: Type[AdvancedFilterSet],
    ) -> models.QuerySet:
        """Return a filtered QuerySet."""
        qs = super(DjangoFilterConnectionField, cls).resolve_queryset(
            connection, iterable, info, args,
        )
        filterset = filterset_class(
            data=tree_input_type_to_data(
                filterset_class,
                args['filter'],
            ),
            queryset=qs,
            request=info.context,
        )
        if filterset.form.is_valid():
            return filterset.qs
        raise ValidationError(filterset.form.errors.as_json())
