"""Functions for converting a FilterSet class to a tree and then to an input type."""

from typing import Dict, List, Optional, Sequence, Type, cast

import graphene
from anytree import Node
from django.db import models
from django.db.models.constants import LOOKUP_SEP
from django_filters import Filter, FilterSet
from graphene.types.unmountedtype import UnmountedType
from graphene_django.filter.utils import get_model_field
from graphene_django.forms.converter import convert_form_field
from stringcase import camelcase, capitalcase


def create_filter_input_type(
    roots: List[Node],
    filter_set_class: Type[FilterSet],
    type_name: str,
) -> Type[graphene.InputObjectType]:
    """Create a filter input type from filter set trees."""
    input_type: Optional[Type[graphene.InputObjectType]] = None

    def get_input_type() -> Optional[Type[graphene.InputObjectType]]:
        return input_type

    input_type = cast(
        Type[graphene.InputObjectType],
        type(
            f'{type_name}FilterInputType',
            (graphene.InputObjectType,),
            {
                **{
                    root.name: graphene.InputField(
                        create_filter_input_subtype(root, filter_set_class, type_name),
                        description=f'{root.name} subfield',
                    )
                    for root in roots
                },
                'or': graphene.InputField(get_input_type, description='Or field'),
                'and': graphene.InputField(get_input_type, description='And field'),
            },
        ),
    )
    return input_type


def create_filter_input_subtype(
    root: Node,
    filter_set_class: Type[FilterSet],
    prefix: str,
) -> Type[graphene.InputObjectType]:
    """Create a filter input subtype from a filter set subtree."""
    if root.height == 1:
        return create_field_filter_input_type(root, filter_set_class, prefix)
    fields: Dict[str, graphene.InputField] = {}
    for child in root.children:
        fields[child.name] = graphene.InputField(
            create_filter_input_subtype(
                child,
                filter_set_class,
                prefix + capitalcase(camelcase(root.name)),
            ),
            description=f'{child.name} subfield',
        )
    return cast(
        Type[graphene.InputObjectType],
        type(
            f'{prefix}{capitalcase(camelcase(root.name))}FilterInputType',
            (graphene.InputObjectType,),
            fields,
        ),
    )


def create_field_filter_input_type(
    root: Node,
    filter_set_class: Type[FilterSet],
    prefix: str,
) -> Type[graphene.InputObjectType]:
    """Create a field filter input type from filter set tree leaves."""
    fields: Dict[str, UnmountedType] = {}
    for lookup_node in root.children:
        fields[lookup_node.name] = get_field(
            filter_set_class,
            lookup_node.filter_name,
            filter_set_class.base_filters[lookup_node.filter_name],
        )
    return cast(
        Type[graphene.InputObjectType],
        type(
            f'{prefix}{capitalcase(camelcase(root.name))}FieldFilterInputType',
            (graphene.InputObjectType,),
            fields,
        ),
    )


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
    field_type = field.InputField()
    field_type.description = getattr(filter_field, 'label')
    return field_type


def filter_set_to_trees(filter_set_class: Type[FilterSet]) -> List[Node]:
    """Convert a FilterSet class to trees."""
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


def try_add_sequence(root: Node, values: Sequence[dict]) -> bool:
    """Try to add a sequence to a tree.

    Return a flag indicating whether the mutation was made.
    """
    if root.name == values[0]['name']:
        for child in root.children:
            is_mutated = try_add_sequence(child, values[1:])
            if is_mutated:
                return True
        root.children = (*root.children, sequence_to_tree(values[1:]))
        return True
    else:
        return False


def sequence_to_tree(values: Sequence[dict]) -> Node:
    """Convert a sequence to a tree."""
    node: Optional[Node] = None
    for value in values:
        node = Node(**value, parent=node)
    return node.root
