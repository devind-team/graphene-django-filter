"""InputObjectType classes for special lookups."""

from typing import Type, cast

import graphene

from .conf import settings


class SearchConfigInputType(graphene.InputObjectType):
    """Input type for the `SearchVector` or `SearchQuery` object config."""

    value = graphene.String(
        required=True,
        description='`SearchVector` or `SearchQuery` object config value',
    )
    is_field = graphene.Boolean(
        default_value=False,
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
    weight = graphene.InputField(SearchVectorWeight, description='Vector weight')


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
                'value': graphene.String(description='Query value'),
                'config': graphene.InputField(SearchConfigInputType, description='Query config'),
                settings.AND_KEY: graphene.InputField(
                    graphene.List(graphene.NonNull(lambda: search_query_input_type)),
                    description='`And` field',
                ),
                settings.OR_KEY: graphene.InputField(
                    graphene.List(graphene.NonNull(lambda: search_query_input_type)),
                    description='`Or` field',
                ),
                settings.NOT_KEY: graphene.InputField(
                    graphene.List(graphene.NonNull(lambda: search_query_input_type)),
                    description='`Not` field',
                ),
            },
        ),
    )
    return search_query_input_type


SearchQueryInputType = create_search_query_input_type()


class SearchQueryFilterInputType(graphene.InputObjectType):
    """Input type for the full text search using the `SearchVector` and `SearchQuery` object."""

    vector = graphene.InputField(SearchVectorInputType, required=True, description='Search vector')
    query = graphene.InputField(SearchQueryInputType, required=True, description='Search query')


class FloatLookupsInputType(graphene.InputObjectType):
    """Input type for float lookups."""

    exact = graphene.Float(description='Is exact')
    gt = graphene.Float(description='Is greater than')
    gte = graphene.Float(description='Is greater than or equal to')
    lt = graphene.Float(description='Is less than')
    lte = graphene.Float(description='Is less than or equal to')


class SearchRankWeightsInputType(graphene.InputObjectType):
    """`SearchRank` object weights.

    Default values are set according to the documentation.
    https://docs.djangoproject.com/en/3.2/ref/contrib/postgres/search/#weighting-queries
    """

    D = graphene.Float(default_value=0.1, description='D letter')
    C = graphene.Float(default_value=0.2, description='C letter')
    B = graphene.Float(default_value=0.4, description='B letter')
    A = graphene.Float(default_value=1.0, description='A letter')


class SearchRankFilterInputType(graphene.InputObjectType):
    """Input type for the full text search using the `SearchRank` object."""

    vector = graphene.InputField(SearchVectorInputType, required=True, description='Search vector')
    query = graphene.InputField(SearchQueryInputType, required=True, description='Search query')
    lookups = graphene.InputField(
        FloatLookupsInputType,
        required=True,
        description='Available lookups',
    )
    weights = graphene.InputField(SearchRankWeightsInputType, description='Search rank weights')
    cover_density = graphene.Boolean(
        default_value=False,
        description='Whether to include coverage density ranking',
    )
    normalization = graphene.Int(description='Search rank normalization')


class TrigramSearchKind(graphene.Enum):
    """Type of the search using trigrams."""

    SIMILARITY = 'similarity'
    DISTANCE = 'distance'


class TrigramFilterInputType(graphene.InputObjectType):
    """Input type for the full text search using similarity or distance of trigram."""

    kind = graphene.InputField(
        TrigramSearchKind,
        default_value=TrigramSearchKind.SIMILARITY,
        description='Type of the search using trigrams',
    )
    lookups = graphene.InputField(
        FloatLookupsInputType,
        required=True,
        description='Available lookups',
    )
    value = graphene.String(required=True, description='Search value')
