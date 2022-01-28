"""Functions for converting a FilterSet class to a tree and then to an input type."""

from typing import Dict, List, Optional, Sequence, Type

import graphene
from anytree import Node
from anytree.exporter import DictExporter
from anytree.importer import DictImporter
from anytree.search import findall_by_attr
from django.db import models
from django.db.models.constants import LOOKUP_SEP
from django_filters import Filter, FilterSet
from graphene.types.unmountedtype import UnmountedType
from graphene_django.filter.utils import get_model_field
from graphene_django.forms.converter import convert_form_field
from stringcase import camelcase, capitalcase


def create_field_filter_input_types(
    type_name: str,
    tree: Node,
    filter_set_class: Type[FilterSet],
) -> Node:
    """Create field filter input types from filter set tree leaves.

    This function return new tree.
    """
    tree_copy = DictImporter().import_(DictExporter().export(tree))
    for field_node in findall_by_attr(tree_copy, name='height', value=1):
        fields: Dict[str, UnmountedType] = {}
        for lookup_node in field_node.children:
            fields[lookup_node.name] = get_field(
                filter_set_class,
                lookup_node.filter_name,
                filter_set_class.base_filters[lookup_node.filter_name],
            )
        input_type = type(
            get_field_filter_input_type_name(type_name, field_node.path),
            (graphene.InputObjectType,),
            fields,
        )
        new_node = Node(name=field_node.name, input_type=input_type)
        if tree_copy == field_node:
            return new_node
        else:
            field_node.parent.children = [
                *(node for node in field_node.parent.children if node is not field_node),
                new_node,
            ]
    return tree_copy


def get_field(filter_set_class: Type[FilterSet], name: str, filter_field: Filter) -> UnmountedType:
    """Return Graphene type from a filter field.

    It is a partial copy of the `get_filtering_args_from_filterset` function from graphene-django.
    https://github.com/graphql-python/graphene-django/blob/caf954861025b9f3d9d3f9c204a7cbbc87352265/graphene_django/filter/utils.py#L11
    """
    model = filter_set_class._meta.model
    form_field: Optional[models.Field] = None
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


def get_field_filter_input_type_name(type_name: str, node_path: Sequence[Node]) -> str:
    """Return field filter input type name from a type name and node path."""
    field_name = ''.join(
        map(
            lambda node: capitalcase(camelcase(node.name)),
            node_path,
        ),
    )
    return f'{type_name.replace("Type", "")}{field_name}FieldFilterInputType'


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
