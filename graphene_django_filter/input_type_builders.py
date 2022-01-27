"""Builders for creation input filter types."""

from typing import Dict, Optional, Type, cast

import graphene
from graphene.types.unmountedtype import UnmountedType
from stringcase import camelcase, capitalcase


class LookupInputTypeBuilder:
    """Builder for creation lookups input type for field."""

    str_lookups = (
        'iexact',
        'contains',
        'icontains',
    )
    float_lookups = (
        'gt',
        'gte',
        'lt',
        'lte',
    )

    def __init__(self, type_name: str, field_name: str) -> None:
        self._type_name = type_name
        self._field_name = field_name
        self._lookups: Dict[str, UnmountedType] = {}
        self._subfields: Dict[str, graphene.Field] = {}

    def add_subfield(
        self,
        subfield_name: str,
        input_type: Type[graphene.InputObjectType],
    ) -> 'LookupInputTypeBuilder':
        """Add subfield for under construction type."""
        self._subfields[subfield_name] = graphene.Field(
            input_type,
            description=f'{subfield_name} subfield',
        )
        return self

    def set_exact(
        self,
        field_type: Type[UnmountedType] = graphene.String,
    ) -> 'LookupInputTypeBuilder':
        """Set exact field for under construction type."""
        self._lookups['exact'] = field_type(description='exact lookup')
        return self

    def set_in(
        self,
        field_type: Type[UnmountedType] = graphene.String,
        is_string: bool = False,
    ) -> 'LookupInputTypeBuilder':
        """Set in field for under construction type."""
        if is_string:
            self._lookups['in'] = graphene.String(description='in lookup')
        else:
            self._lookups['in'] = graphene.List(field_type, description='in lookup')
        return self

    def set_str_lookup(self, lookup: str) -> 'LookupInputTypeBuilder':
        """Set str field for under construction type."""
        assert lookup in self.str_lookups,\
            f'{lookup} is invalid. Valid lookups are [{", ".join(self.str_lookups)}]'
        self._lookups[lookup] = graphene.String(description=f'{lookup} lookup')
        return self

    def set_float_lookup(self, lookup: str) -> 'LookupInputTypeBuilder':
        """Set float field for under construction type."""
        assert lookup in self.float_lookups,\
            f'{lookup} is invalid. Valid lookups are [{", ".join(self.float_lookups)}]'
        self._lookups[lookup] = graphene.Float(description=f'{lookup} lookup')
        return self

    def build(self) -> Type[graphene.InputObjectType]:
        """Build input type."""
        return cast(
            Type[graphene.InputObjectType],
            type(
                f'{self._type_name}{capitalcase(camelcase(self._field_name))}FilterInputType',
                (graphene.InputObjectType,),
                {**self._lookups, **self._subfields},
            ),
        )


class FilterInputTypeBuilder:
    """Builder for creation filter input type."""

    def __init__(self, type_name: str) -> None:
        self._type_name = type_name
        self._lookup_input_types: Dict[str, Type[graphene.InputObjectType]] = {}
        self._or: bool = False
        self._and: bool = False

    def add_lookup_input_type(
        self,
        field_name: str,
        lookup_input_type: Type[graphene.InputObjectType],
    ) -> 'FilterInputTypeBuilder':
        """Add lookup input type field."""
        self._lookup_input_types[field_name] = lookup_input_type
        return self

    def set_or(self, _or: bool) -> 'FilterInputTypeBuilder':
        """Set the flag which determines whether to add the field or."""
        self._or = _or
        return self

    def set_and(self, _and: bool) -> 'FilterInputTypeBuilder':
        """Set the flag which determines whether to add the field and."""
        self._and = _and
        return self

    def build(self) -> Type[graphene.InputObjectType]:
        """Build input type."""
        name = f'{self._type_name}FilterInputType'
        attrs = {k: graphene.Field(v) for k, v in self._lookup_input_types.items()}
        input_type: Optional[Type[graphene.InputObjectType]] = None

        def get_input_type() -> Optional[Type[graphene.InputObjectType]]:
            return input_type

        if self._or:
            attrs['or'] = graphene.Field(get_input_type, description='Or field')
        if self._and:
            attrs['and'] = graphene.Field(get_input_type, description='And field')
        input_type = cast(
            Type[graphene.InputObjectType],
            type(
                name,
                (graphene.InputObjectType,),
                attrs,
            ),
        )
        return input_type
