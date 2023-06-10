"""Module for converting a AdvancedFilterSet class to filter arguments."""

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


class FilterArgumentsFactory:
    """Factory for creating filter arguments."""

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

    input_object_types: Dict[str, Type[graphene.InputObjectType]] = {}

    def __init__(self, filterset_class: Type[AdvancedFilterSet], input_type_prefix: str) -> None:
        self.filterset_class = filterset_class
        self.input_type_prefix = input_type_prefix
        self.filter_input_type_name = f'{self.input_type_prefix}FilterInputType'

    @property
    def arguments(self) -> Dict[str, graphene.Argument]:
        """Inspect a FilterSet and produce the arguments to pass to a Graphene Field.

        These arguments will be available to filter against in the GraphQL.
        """
        input_object_type = self.input_object_types.get(
            self.filter_input_type_name,
            self.create_filter_input_type(
                self.filterset_to_trees(self.filterset_class),
            ),
        )
        return {
            settings.FILTER_KEY: graphene.Argument(
                input_object_type,
                description='Advanced filter field',
            ),
        }

    def create_filter_input_type(self, roots: List[Node]) -> Type[graphene.InputObjectType]:
        """Create a filter input type from filter set trees."""
        self.input_object_types[self.filter_input_type_name] = cast(
            Type[graphene.InputObjectType],
            type(
                self.filter_input_type_name,
                (graphene.InputObjectType,),
                {
                    **{
                        root.name: self.create_filter_input_subfield(
                            root,
                            self.input_type_prefix,
                            f'`{pascalcase(root.name)}` field',
                        )
                        for root in roots
                    },
                    settings.AND_KEY: graphene.InputField(
                        graphene.List(lambda: self.input_object_types[self.filter_input_type_name]),
                        description='`And` field',
                    ),
                    settings.OR_KEY: graphene.InputField(
                        graphene.List(lambda: self.input_object_types[self.filter_input_type_name]),
                        description='`Or` field',
                    ),
                    settings.NOT_KEY: graphene.InputField(
                        lambda: self.input_object_types[self.filter_input_type_name],
                        description='`Not` field',
                    ),
                },
            ),
        )
        return self.input_object_types[self.filter_input_type_name]

    def create_filter_input_subfield(
        self,
        root: Node,
        prefix: str,
        description: str,
    ) -> graphene.InputField:
        """Create a filter input subfield from a filter set subtree."""
        fields: Dict[str, graphene.InputField] = {}
        if root.name in self.SPECIAL_FILTER_INPUT_TYPES_FACTORIES:
            return self.SPECIAL_FILTER_INPUT_TYPES_FACTORIES[root.name]()
        else:
            for child in root.children:
                if child.height == 0:
                    filter_name = f'{LOOKUP_SEP}'.join(
                        node.name for node in child.path
                        if node.name != django_settings.DEFAULT_LOOKUP_EXPR
                    )
                    fields[child.name] = self.get_field(
                        filter_name,
                        self.filterset_class.base_filters[filter_name],
                    )
                else:
                    fields[child.name] = self.create_filter_input_subfield(
                        child,
                        prefix + pascalcase(root.name),
                        f'`{pascalcase(child.name)}` subfield',
                    )
        return graphene.InputField(
            self.create_input_object_type(
                f'{prefix}{pascalcase(root.name)}FilterInputType',
                fields,
            ),
            description=description,
        )

    @classmethod
    def create_input_object_type(
        cls,
        name: str,
        fields: Dict[str, Any],
    ) -> Type[graphene.InputObjectType]:
        """Create an inheritor for the `InputObjectType` class."""
        if name in cls.input_object_types:
            return cls.input_object_types[name]
        cls.input_object_types[name] = cast(
            Type[graphene.InputObjectType],
            type(
                name,
                (graphene.InputObjectType,),
                fields,
            ),
        )
        return cls.input_object_types[name]

    def get_field(self, name: str, filter_field: Filter) -> graphene.InputField:
        """Return Graphene input field from a filter field.

        It is a partial copy of the `get_filtering_args_from_filterset` function
        from graphene-django.
        https://github.com/graphql-python/graphene-django/blob/caf954861025b9f3d9d3f9c204a7cbbc87352265/graphene_django/filter/utils.py#L11
        """
        model = self.filterset_class._meta.model
        form_field: Optional[models.Field] = None
        filter_type: str = filter_field.lookup_expr
        if name in getattr(self.filterset_class, 'declared_filters'):
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

    @classmethod
    def filterset_to_trees(cls, filterset_class: Type[AdvancedFilterSet]) -> List[Node]:
        """Convert a FilterSet class to trees."""
        trees: List[Node] = []
        for filter_value in filterset_class.base_filters.values():
            values = (*filter_value.field_name.split(LOOKUP_SEP), filter_value.lookup_expr)
            if len(trees) == 0 or not any(cls.try_add_sequence(tree, values) for tree in trees):
                trees.append(cls.sequence_to_tree(values))
        return trees

    @classmethod
    def try_add_sequence(cls, root: Node, values: Sequence[str]) -> bool:
        """Try to add a sequence to a tree.

        Return a flag indicating whether the mutation was made.
        """
        if root.name == values[0]:
            for child in root.children:
                is_mutated = cls.try_add_sequence(child, values[1:])
                if is_mutated:
                    return True
            root.children = (*root.children, cls.sequence_to_tree(values[1:]))
            return True
        else:
            return False

    @staticmethod
    def sequence_to_tree(values: Sequence[str]) -> Node:
        """Convert a sequence to a tree."""
        node: Optional[Node] = None
        for value in values:
            node = Node(name=value, parent=node)
        return node.root
