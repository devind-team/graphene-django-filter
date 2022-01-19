"""Builders for creation input filter types."""

from typing import Dict, Type, cast

import graphene
from graphene.types.unmountedtype import UnmountedType
from stringcase import camelcase, capitalcase


class LookupInputTypeBuilder:
    """Builder for creation lookups input type for field."""

    def __init__(self, type_name: str, field_name: str) -> None:
        self._type_name = type_name
        self._field_name = field_name
        self._attrs: Dict[str, UnmountedType] = {}

    def set_exact(self) -> 'LookupInputTypeBuilder':
        """Set exact field for under construction type."""
        self._attrs['exact'] = graphene.String(description='exact lookup')
        return self

    def set_iexact(self) -> 'LookupInputTypeBuilder':
        """Set iexact field for under construction type."""
        self._attrs['iexact'] = graphene.String(description='iexact lookup')
        return self

    def set_contains(self) -> 'LookupInputTypeBuilder':
        """Set contains field for under construction type."""
        self._attrs['contains'] = graphene.String(description='contains lookup')
        return self

    def set_icontains(self) -> 'LookupInputTypeBuilder':
        """Set icontains field for under construction type."""
        self._attrs['icontains'] = graphene.String(description='icontains lookup')
        return self

    def set_gt(self) -> 'LookupInputTypeBuilder':
        """Set gt field for under construction type."""
        self._attrs['gt'] = graphene.Float(description='gt lookup')
        return self

    def set_gte(self) -> 'LookupInputTypeBuilder':
        """Set gte field for under construction type."""
        self._attrs['gte'] = graphene.Float(description='gte lookup')
        return self

    def set_lt(self) -> 'LookupInputTypeBuilder':
        """Set lt field for under construction type."""
        self._attrs['lt'] = graphene.Float(description='lt lookup')
        return self

    def set_lte(self) -> 'LookupInputTypeBuilder':
        """Set lte field for under construction type."""
        self._attrs['lte'] = graphene.Float(description='lte lookup')
        return self

    def set_in(
        self,
        field_type: Type[UnmountedType] = graphene.String,
        is_string: bool = False,
    ) -> 'LookupInputTypeBuilder':
        """Set in field for under construction type."""
        if is_string:
            self._attrs['in'] = graphene.String(description='in lookup')
        else:
            self._attrs['in'] = graphene.List(field_type, description='in lookup')
        return self

    def build(self) -> Type[graphene.InputObjectType]:
        """Build input type."""
        return cast(
            Type[graphene.InputObjectType],
            type(
                f'{self._type_name}{capitalcase(camelcase(self._field_name))}FilterInputType',
                (graphene.InputObjectType,),
                self._attrs,
            ),
        )
