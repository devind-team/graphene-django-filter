"""Functions for converting a FilterSet class to a tree and then to an input type."""

from typing import List, Optional, Sequence, Type

import graphene
from anytree import Node
from django.db.models import Field
from django.db.models.constants import LOOKUP_SEP
from django_filters import Filter, FilterSet
from graphene.types.unmountedtype import UnmountedType
from graphene_django.filter.utils import get_model_field
from graphene_django.forms.converter import convert_form_field


def get_field(filter_set_class: Type[FilterSet], name: str, filter_field: Filter) -> UnmountedType:
    """Return Graphene type from filter field.

    It is a partial copy of the get_filtering_args_from_filterset method from graphene-django.
    https://github.com/graphql-python/graphene-django/blob/775644b5369bdc5fbb45d3535ae391a069ebf9d4/graphene_django/filter/utils.py#L25
    """
    model = filter_set_class._meta.model
    form_field: Optional[Field] = None
    filter_type: str = filter_field.lookup_expr
    if name in getattr(filter_set_class, 'declared_filters'):
        form_field = filter_field.field
        field = convert_form_field(form_field)
    else:
        model_field = get_model_field(model, filter_field.field_name)
        if filter_type != 'isnull' and hasattr(model_field, 'formfield'):
            form_field = model_field.formfield(
                required=filter_field.extra.get('required', False),
            )
        if not form_field:
            form_field = filter_field.field
        field = convert_form_field(form_field)
    if filter_type in ('in', 'range'):
        field = graphene.List(field.get_type())
    field_type = field.Argument()
    field_type.description = getattr(filter_field, 'label')
    return field_type


def filter_set_to_trees(filter_set_class: Type[FilterSet]) -> List[Node]:
    """Convert a FilterSet class to a tree."""
    trees: List[Node] = []
    for filter_name, filter_value in filter_set_class.base_filters.items():
        values = [
            {'name': name}
            for name in (*filter_value.field_name.split(LOOKUP_SEP), filter_value.lookup_expr)
        ]
        values[-1]['filter_name'] = filter_name
        if len(trees) == 0 or not any([try_add_sequence(tree, values) for tree in trees]):
            trees.append(sequence_to_tree(values))
    return trees


def try_add_sequence(tree: Node, values: Sequence[dict]) -> bool:
    """Try to add a sequence to a tree.

    Return a flag indicating whether the mutation was made.
    """
    if tree.name == values[0]['name']:
        for child in tree.children:
            is_mutated = try_add_sequence(child, values[1:])
            if is_mutated:
                return True
        tree.children = (*tree.children, sequence_to_tree(values[1:]))
        return True
    else:
        return False


def sequence_to_tree(values: Sequence[dict]) -> Node:
    """Convert a sequence to a tree."""
    node: Optional[Node] = None
    for value in values:
        node = Node(**value, parent=node)
    return node.root
