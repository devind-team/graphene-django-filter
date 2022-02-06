"""Functions for creating a FilterSet class."""

from typing import Optional, Type

from graphene_django.filter.filterset import custom_filterset_factory, setup_filterset
from graphene_django.filter.utils import replace_csv_filters

from .filterset import AdvancedFilterSet


def get_filterset_class(
    filterset_class: Optional[Type[AdvancedFilterSet]],
    **meta
) -> Type[AdvancedFilterSet]:
    """Get a class to be used as a FilterSet.

    It is a partial copy of the `get_filterset_class` function from graphene-django.
    https://github.com/graphql-python/graphene-django/blob/caf954861025b9f3d9d3f9c204a7cbbc87352265/graphene_django/filter/utils.py#L56
    """
    if filterset_class:
        graphene_filterset_class = setup_filterset(filterset_class)
    else:
        graphene_filterset_class = custom_filterset_factory(
            filterset_base_class=AdvancedFilterSet,
            **meta
        )
    replace_csv_filters(graphene_filterset_class)
    return graphene_filterset_class
