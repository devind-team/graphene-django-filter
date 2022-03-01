"""Functions for converting tree data into data suitable for the FilterSet."""

from typing import Any, Dict, List, Type, Union

from django.contrib.postgres.search import (
    SearchQuery,
    SearchRank,
    SearchVector,
    TrigramDistance,
    TrigramSimilarity,
)
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models.constants import LOOKUP_SEP
from django_filters.conf import settings as django_settings
from graphene.types.inputobjecttype import InputObjectTypeContainer
from graphene_django_filter.filters import SearchQueryFilter, SearchRankFilter, TrigramFilter
from graphene_django_filter.input_types import (
    SearchConfigInputType,
    SearchQueryFilterInputType,
    SearchQueryInputType,
    SearchRankFilterInputType,
    SearchRankWeightsInputType,
    SearchVectorInputType,
    TrigramFilterInputType,
    TrigramSearchKind,
)

from .conf import settings
from .filterset import AdvancedFilterSet


def tree_input_type_to_data(
    filterset_class: Type[AdvancedFilterSet],
    tree_input_type: InputObjectTypeContainer,
    prefix: str = '',
) -> Dict[str, Any]:
    """Convert a tree_input_type to a FilterSet data."""
    result: Dict[str, Any] = {}
    for key, value in tree_input_type.items():
        if key in ('and', 'or'):
            result[key] = [tree_input_type_to_data(filterset_class, subtree) for subtree in value]
        elif key == 'not':
            result[key] = tree_input_type_to_data(filterset_class, value)
        else:
            result.update(
                create_data(
                    (prefix + LOOKUP_SEP + key if prefix else key).replace(
                        LOOKUP_SEP + django_settings.DEFAULT_LOOKUP_EXPR, '',
                    ),
                    value,
                    filterset_class,
                ),
            )
    return result


def create_data(key: str, value: Any, filterset_class: Type[AdvancedFilterSet]) -> Dict[str, Any]:
    """Create data from a key and a value."""
    for factory_key, factory in DATA_FACTORIES.items():
        if factory_key in key:
            return factory(value, key, filterset_class)
    if isinstance(value, InputObjectTypeContainer):
        return tree_input_type_to_data(filterset_class, value, key)
    else:
        return {key: value}


def create_search_query_data(
    input_type: SearchQueryFilterInputType,
    key: str,
    filterset_class: Type[AdvancedFilterSet],
) -> Dict[str, SearchQueryFilter.Value]:
    """Create a data for the `SearchQueryFilter` class."""
    return {
        key: SearchQueryFilter.Value(
            annotation_value=create_search_vector(input_type.vector, filterset_class),
            search_value=create_search_query(input_type.query),
        ),
    }


def create_search_rank_data(
    input_type: Union[SearchRankFilterInputType, InputObjectTypeContainer],
    key: str,
    filterset_class: Type[AdvancedFilterSet],
) -> Dict[str, SearchRankFilter.Value]:
    """Create a data for the `SearchRankFilter` class."""
    rank_data = {}
    for lookup, value in input_type.lookups.items():
        search_rank_data = {
            'vector': create_search_vector(input_type.vector, filterset_class),
            'query': create_search_query(input_type.query),
            'cover_density': input_type.cover_density,
        }
        weights = input_type.get('weights', None)
        if weights:
            search_rank_data['weights'] = create_search_rank_weights(weights)
        normalization = input_type.get('normalization', None)
        if normalization:
            search_rank_data['normalization'] = normalization
        k = (key + LOOKUP_SEP + lookup).replace(
            LOOKUP_SEP + django_settings.DEFAULT_LOOKUP_EXPR, '',
        )
        rank_data[k] = SearchRankFilter.Value(
            annotation_value=SearchRank(**search_rank_data),
            search_value=value,
        )
    return rank_data


def create_trigram_data(
    input_type: TrigramFilterInputType,
    key: str,
    *args
) -> Dict[str, TrigramFilter.Value]:
    """Create a data for the `TrigramFilter` class."""
    trigram_data = {}
    if input_type.kind == TrigramSearchKind.SIMILARITY:
        trigram_class = TrigramSimilarity
    else:
        trigram_class = TrigramDistance
    for lookup, value in input_type.lookups.items():
        k = (key + LOOKUP_SEP + lookup).replace(
            LOOKUP_SEP + django_settings.DEFAULT_LOOKUP_EXPR, '',
        )
        trigram_data[k] = TrigramFilter.Value(
            annotation_value=trigram_class(
                LOOKUP_SEP.join(key.split(LOOKUP_SEP)[:-1]),
                input_type.value,
            ),
            search_value=value,
        )
    return trigram_data


def create_search_vector(
    input_type: Union[SearchVectorInputType, InputObjectTypeContainer],
    filterset_class: Type[AdvancedFilterSet],
) -> SearchVector:
    """Create an object of the `SearchVector` class."""
    validate_search_vector_fields(filterset_class, input_type.fields)
    search_vector_data = {}
    config = input_type.get('config', None)
    if config:
        search_vector_data['config'] = create_search_config(config)
    weight = input_type.get('weight', None)
    if weight:
        search_vector_data['weight'] = weight.value
    return SearchVector(*input_type.fields, **search_vector_data)


def create_search_query(
    input_type: Union[SearchQueryInputType, InputObjectTypeContainer],
) -> SearchQuery:
    """Create an object of the `SearchQuery` class."""
    validate_search_query(input_type)
    value = input_type.get('value', None)
    if value:
        config = input_type.get('config', None)
        if config:
            search_query = SearchQuery(input_type.value, config=create_search_config(config))
        else:
            search_query = SearchQuery(input_type.value)
    else:
        search_query = None
    and_search_query = None
    for and_input_type in input_type.get(settings.AND_KEY, []):
        if and_search_query is None:
            and_search_query = create_search_query(and_input_type)
        else:
            and_search_query = and_search_query & create_search_query(and_input_type)
    or_search_query = None
    for or_input_type in input_type.get(settings.OR_KEY, []):
        if or_search_query is None:
            or_search_query = create_search_query(or_input_type)
        else:
            or_search_query = or_search_query | create_search_query(or_input_type)
    not_input_type = input_type.get(settings.NOT_KEY, None)
    not_search_query = create_search_query(not_input_type) if not_input_type else None
    valid_queries = (
        q for q in (and_search_query, or_search_query, not_search_query) if q is not None
    )
    for valid_query in valid_queries:
        search_query = search_query & valid_query if search_query else valid_query
    return search_query


def create_search_config(input_type: SearchConfigInputType) -> Union[str, models.F]:
    """Create a `SearchVector` or `SearchQuery` object config."""
    return models.F(input_type.value) if input_type.is_field else input_type.value


def create_search_rank_weights(input_type: SearchRankWeightsInputType) -> List[float]:
    """Create a search rank weights list."""
    return [input_type.D, input_type.C, input_type.B, input_type.A]


def validate_search_vector_fields(
    filterset_class: Type[AdvancedFilterSet],
    fields: List[str],
) -> None:
    """Validate that fields is included in full text search fields."""
    full_text_search_fields = filterset_class.get_full_text_search_fields()
    for field in fields:
        if field not in full_text_search_fields:
            raise ValidationError(f'The `{field}` field is not included in full text search fields')


def validate_search_query(
    input_type: Union[SearchQueryInputType, InputObjectTypeContainer],
) -> None:
    """Validate that search query contains at least one required field."""
    if all([
        'value' not in input_type,
        settings.AND_KEY not in input_type,
        settings.OR_KEY not in input_type,
        settings.NOT_KEY not in input_type,
    ]):
        raise ValidationError(
            'The search query must contains at least one required field '
            f'such as `value`, `{settings.AND_KEY}`, `{settings.OR_KEY}`, `{settings.NOT_KEY}`.',
        )


DATA_FACTORIES = {
    SearchQueryFilter.postfix: create_search_query_data,
    SearchRankFilter.postfix: create_search_rank_data,
    TrigramFilter.postfix: create_trigram_data,
}
