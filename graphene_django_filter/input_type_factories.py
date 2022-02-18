"""Functions for converting a FilterSet class to a tree and then to an input type."""

from typing import Any, Dict, List, Optional, Sequence, Type, cast

import graphene
from anytree import Node
from django.db import models
from django.db.models.constants import LOOKUP_SEP
from django_filters import Filter
from django_filters.conf import settings as django_settings
from graphene_django.filter.utils import get_model_field
from graphene_django.forms.converter import convert_form_field
from stringcase import pascalcase

from .conf import settings
from .filters import SearchQueryFilter, SearchRankFilter, TrigramFilter
from .filterset import AdvancedFilterSet
from .input_types import (
    SearchQueryFilterInputType,
    SearchRankFilterInputType,
    TrigramFilterInputType,
)


def get_filtering_args_from_filterset(
    filterset_class: Type[AdvancedFilterSet],
    node_type: Type[graphene.ObjectType],
) -> Dict[str, graphene.Argument]:
    """Inspect a FilterSet and produce the arguments to pass to a Graphene Field.

    These arguments will be available to filter against in the GraphQL.
    """
    return {
        settings.FILTER_KEY: graphene.Argument(
            create_filter_input_type(
                filterset_to_trees(filterset_class),
                filterset_class,
                node_type.__name__.replace('Type', ''),
            ), description='Advanced filter field',
        ),
    }


def create_filter_input_type(
    roots: List[Node],
    filterset_class: Type[AdvancedFilterSet],
    type_name: str,
) -> Type[graphene.InputObjectType]:
    """Create a filter input type from filter set trees."""
    input_type = cast(
        Type[graphene.InputObjectType],
        type(
            f'{type_name}FilterInputType',
            (graphene.InputObjectType,),
            {
                **{
                    root.name: create_filter_input_subfield(
                        root,
                        filterset_class,
                        type_name,
                        f'`{pascalcase(root.name)}` field',
                    )
                    for root in roots
                },
                settings.AND_KEY: graphene.InputField(
                    graphene.List(lambda: input_type),
                    description='`And` field',
                ),
                settings.OR_KEY: graphene.InputField(
                    graphene.List(lambda: input_type),
                    description='`Or` field',
                ),
                settings.NOT_KEY: graphene.InputField(
                    lambda: input_type,
                    description='`Not` field',
                ),
            },
        ),
    )
    return input_type


def create_filter_input_subfield(
    root: Node,
    filterset_class: Type[AdvancedFilterSet],
    prefix: str,
    description: str,
) -> graphene.InputField:
    """Create a filter input subfield from a filter set subtree."""
    fields: Dict[str, graphene.InputField] = {}
    if root.name in SPECIAL_FILTER_INPUT_TYPES_FACTORIES:
        return SPECIAL_FILTER_INPUT_TYPES_FACTORIES[root.name]()
    else:
        for child in root.children:
            if child.height == 0:
                filter_name = f'{LOOKUP_SEP}'.join(
                    node.name for node in child.path
                    if node.name != django_settings.DEFAULT_LOOKUP_EXPR
                )
                fields[child.name] = get_field(
                    filterset_class,
                    filter_name,
                    filterset_class.base_filters[filter_name],
                )
            else:
                fields[child.name] = create_filter_input_subfield(
                    child,
                    filterset_class,
                    prefix + pascalcase(root.name),
                    f'`{pascalcase(child.name)}` subfield',
                )
    return graphene.InputField(
        create_input_object_type(
            f'{prefix}{pascalcase(root.name)}FilterInputType',
            fields,
        ),
        description=description,
    )


SPECIAL_FILTER_INPUT_TYPES_FACTORIES = {
    SearchQueryFilter.postfix: lambda: graphene.InputField(
        SearchQueryFilterInputType,
        description='Field for the full text search using '
                    'the `SearchVector` and `SearchQuery` object',
    ),
    SearchRankFilter.postfix: lambda: graphene.InputField(
        SearchRankFilterInputType,
        description='Field for the full text search using the `SearchRank` object',
    ),
    TrigramFilter.postfix: lambda: graphene.InputField(
        TrigramFilterInputType,
        description='Field for the full text search using similarity or distance of trigram',
    ),
}


def create_input_object_type(name: str, fields: Dict[str, Any]) -> Type[graphene.InputObjectType]:
    """Create an inheritor for the `InputObjectType` class."""
    return cast(
        Type[graphene.InputObjectType],
        type(
            name,
            (graphene.InputObjectType,),
            fields,
        ),
    )


def get_field(
    filterset_class: Type[AdvancedFilterSet],
    name: str,
    filter_field: Filter,
) -> graphene.InputField:
    """Return Graphene input field from a filter field.

    It is a partial copy of the `get_filtering_args_from_filterset` function from graphene-django.
    https://github.com/graphql-python/graphene-django/blob/caf954861025b9f3d9d3f9c204a7cbbc87352265/graphene_django/filter/utils.py#L11
    """
    model = filterset_class._meta.model
    form_field: Optional[models.Field] = None
    filter_type: str = filter_field.lookup_expr
    if name in getattr(filterset_class, 'declared_filters'):
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
    field_type.description = getattr(filter_field, 'label') or \
        f'`{pascalcase(filter_field.lookup_expr)}` lookup'
    return field_type


def filterset_to_trees(filterset_class: Type[AdvancedFilterSet]) -> List[Node]:
    """Convert a FilterSet class to trees."""
    trees: List[Node] = []
    for filter_value in filterset_class.base_filters.values():
        values = (*filter_value.field_name.split(LOOKUP_SEP), filter_value.lookup_expr)
        if len(trees) == 0 or not any([try_add_sequence(tree, values) for tree in trees]):
            trees.append(sequence_to_tree(values))
    return trees


def try_add_sequence(root: Node, values: Sequence[str]) -> bool:
    """Try to add a sequence to a tree.

    Return a flag indicating whether the mutation was made.
    """
    if root.name == values[0]:
        for child in root.children:
            is_mutated = try_add_sequence(child, values[1:])
            if is_mutated:
                return True
        root.children = (*root.children, sequence_to_tree(values[1:]))
        return True
    else:
        return False


def sequence_to_tree(values: Sequence[str]) -> Node:
    """Convert a sequence to a tree."""
    node: Optional[Node] = None
    for value in values:
        node = Node(name=value, parent=node)
    return node.root
