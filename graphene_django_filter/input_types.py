"""InputObjectType classes for special lookups."""

from typing import Type, cast

import graphene

from .conf import settings


class SearchConfigInputType(graphene.InputObjectType):
    """Input type for the `SearchVector` or `SearchQuery` object config."""

    value = graphene.String()
    is_field = graphene.Boolean(default=False)


class SearchVectorWeight(graphene.Enum):
    """Weight of the `SearchVector` object."""

    A = 'A'
    B = 'B'
    C = 'C'
    D = 'D'


class SearchVectorInputType(graphene.InputObjectType):
    """Input type for creating the `SearchVector` object."""

    fields = graphene.List(graphene.NonNull(graphene.String), required=True)
    config = graphene.InputField(SearchConfigInputType)
    weight = graphene.InputField(SearchVectorWeight)


class SearchQueryType(graphene.Enum):
    """Search type of the `SearchQuery` object."""

    PLAIN = 'plain'
    PHRASE = 'phrase'
    RAW = 'raw'
    WEBSEARCH = 'websearch'


def create_search_query_input_type() -> Type[graphene.InputObjectType]:
    """Return input type for creating the `SearchQuery` object."""
    search_query_input_type = cast(
        Type[graphene.InputObjectType],
        type(
            'SearchQueryInputType',
            (graphene.InputObjectType,),
            {
                '__doc__': 'Input type for creating the `SearchQuery` object.',
                'value': graphene.String(required=True),
                'config': graphene.InputField(SearchConfigInputType),
                settings.AND_KEY: graphene.List(lambda: search_query_input_type),
                settings.OR_KEY: graphene.List(lambda: search_query_input_type),
                settings.NOT_KEY: graphene.List(lambda: search_query_input_type),
            },
        ),
    )
    return search_query_input_type


SearchQueryInputType = create_search_query_input_type()


class SearchQueryFilterInputType(graphene.InputObjectType):
    """Input type for the full text search using the `SearchQueryFilter` class."""

    vector = graphene.InputField(SearchVectorInputType)
    query = graphene.InputField(SearchQueryInputType)


class FloatLookups(graphene.InputObjectType):
    """Input type for float lookups."""

    exact = graphene.Float()
    gt = graphene.Float()
    gte = graphene.Float()
    lt = graphene.Float()
    lte = graphene.Float()


class SearchRankFilterInputType(graphene.InputObjectType):
    """Input type for the full text search using the `SearchRankFilter` class."""

    vector = graphene.InputField(SearchVectorInputType)
    query = graphene.InputField(SearchQueryInputType)
    value = graphene.InputField(FloatLookups)


class TrigramSearchType(graphene.Enum):
    """Type of the search using trigrams."""

    SIMILARITY = 'similarity'
    DISTANCE = 'distance'


class TrigramFilterInputType(graphene.InputObjectType):
    """Input type for the full text search using the `TrigramFilter` class."""

    kind = graphene.InputField(TrigramSearchType)
    value = graphene.InputField(FloatLookups)
