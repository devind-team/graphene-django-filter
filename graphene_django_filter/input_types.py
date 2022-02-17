"""InputObjectType classes for special lookups."""

from typing import Type, cast

import graphene

from .conf import settings


class SearchConfigInputType(graphene.InputObjectType):
    """Input type for the `SearchVector` or `SearchQuery` object config."""

    value = graphene.String(description='`SearchVector` or `SearchQuery` object config value')
    is_field = graphene.Boolean(
        default=False,
        description='Whether to wrap the value with the F object',
    )


class SearchVectorWeight(graphene.Enum):
    """Weight of the `SearchVector` object."""

    A = 'A'
    B = 'B'
    C = 'C'
    D = 'D'


class SearchVectorInputType(graphene.InputObjectType):
    """Input type for creating the `SearchVector` object."""

    fields = graphene.InputField(
        graphene.List(graphene.NonNull(graphene.String)),
        required=True,
        description='Field names of vector',
    )
    config = graphene.InputField(SearchConfigInputType, description='Vector config'),
    weight = graphene.InputField(SearchVectorWeight, 'Vector weight')


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
                'value': graphene.String(required=True, description='Query value'),
                'config': graphene.InputField(SearchConfigInputType, description='Query config'),
                settings.AND_KEY: graphene.InputField(
                    graphene.List(lambda: search_query_input_type),
                    description='`And` field',
                ),
                settings.OR_KEY: graphene.InputField(
                    graphene.List(lambda: search_query_input_type),
                    description='`Or` field',
                ),
                settings.NOT_KEY: graphene.InputField(
                    graphene.List(lambda: search_query_input_type),
                    description='`Not` field',
                ),
            },
        ),
    )
    return search_query_input_type


SearchQueryInputType = create_search_query_input_type()


class SearchQueryFilterInputType(graphene.InputObjectType):
    """Input type for the full text search using the `SearchQueryFilter` class."""

    vector = graphene.InputField(SearchVectorInputType, description='Search vector')
    query = graphene.InputField(SearchQueryInputType, description='Search query')


class FloatLookups(graphene.InputObjectType):
    """Input type for float lookups."""

    exact = graphene.Float('Is exact')
    gt = graphene.Float('Is greater than')
    gte = graphene.Float('Is greater than or equal to')
    lt = graphene.Float('Is less than')
    lte = graphene.Float('Is less than or equal to')


class SearchRankFilterInputType(graphene.InputObjectType):
    """Input type for the full text search using the `SearchRankFilter` class."""

    vector = graphene.InputField(SearchVectorInputType, description='Search vector')
    query = graphene.InputField(SearchQueryInputType, description='Search query')
    value = graphene.InputField(FloatLookups, description='Available lookups')


class TrigramSearchType(graphene.Enum):
    """Type of the search using trigrams."""

    SIMILARITY = 'similarity'
    DISTANCE = 'distance'


class TrigramFilterInputType(graphene.InputObjectType):
    """Input type for the full text search using the `TrigramFilter` class."""

    kind = graphene.InputField(TrigramSearchType, description='Type of the search using trigrams')
    value = graphene.InputField(FloatLookups, description='Available lookups')
