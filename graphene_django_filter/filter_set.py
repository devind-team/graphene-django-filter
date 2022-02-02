"""`AdvancedFilterSet` class module.

Use the `AdvancedFilterSet` class from this module instead of the `FilterSet` from django-filter.
"""

from typing import Any, Dict

from django.db.models.constants import LOOKUP_SEP
from django_filters.filterset import BaseFilterSet, FilterSetMetaclass
from graphene.types.inputobjecttype import InputObjectTypeContainer


def tree_input_type_to_data(
    tree_input_type: InputObjectTypeContainer,
    prefix: str = '',
) -> Dict[str, Any]:
    """Convert a tree_input_type to a FilterSet data."""
    result: Dict[str, Any] = {}
    for key, value in tree_input_type.items():
        if key in ('or', 'and'):
            result[key] = tree_input_type_to_data(value)
        else:
            k = prefix + LOOKUP_SEP + key if prefix else key
            if isinstance(value, InputObjectTypeContainer):
                result.update(tree_input_type_to_data(value, k))
            else:
                result[k] = value
    return result


class AdvancedFilterSet(BaseFilterSet, metaclass=FilterSetMetaclass):
    """Allow you to use advanced filters with `or` and `and` expressions."""

    pass
