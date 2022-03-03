"""Additional filters for special lookups."""

from typing import Any, Callable, NamedTuple, Optional, Union

from django.contrib.postgres.search import (
    SearchQuery,
    SearchRank,
    SearchVector,
    TrigramDistance,
    TrigramSimilarity,
)
from django.db import models
from django.db.models.constants import LOOKUP_SEP
from django_filters import Filter
from django_filters.constants import EMPTY_VALUES


class AnnotatedFilter(Filter):
    """Filter with a QuerySet object annotation."""

    class Value(NamedTuple):
        annotation_value: Any
        search_value: Any

    postfix = 'annotated'

    def __init__(
        self,
        field_name: Optional[str] = None,
        lookup_expr: Optional[str] = None,
        *,
        label: Optional[str] = None,
        method: Optional[Union[str, Callable]] = None,
        distinct: bool = False,
        exclude: bool = False,
        **kwargs
    ) -> None:
        super().__init__(
            field_name,
            lookup_expr,
            label=label,
            method=method,
            distinct=distinct,
            exclude=exclude,
            **kwargs
        )
        self.filter_counter = 0

    @property
    def annotation_name(self) -> str:
        """Return the name used for the annotation."""
        return f'{self.field_name}_{self.postfix}_{self.creation_counter}_{self.filter_counter}'

    def filter(self, qs: models.QuerySet, value: Value) -> models.QuerySet:
        """Filter a QuerySet using annotation."""
        if value in EMPTY_VALUES:
            return qs
        if self.distinct:
            qs = qs.distinct()
        annotation_name = self.annotation_name
        self.filter_counter += 1
        qs = qs.annotate(**{annotation_name: value.annotation_value})
        lookup = f'{annotation_name}{LOOKUP_SEP}{self.lookup_expr}'
        return self.get_method(qs)(**{lookup: value.search_value})


class SearchQueryFilter(AnnotatedFilter):
    """Full text search filter using the `SearchVector` and `SearchQuery` object."""

    class Value(NamedTuple):
        annotation_value: SearchVector
        search_value: SearchQuery

    postfix = 'search_query'
    available_lookups = ('exact',)

    def filter(self, qs: models.QuerySet, value: Value) -> models.QuerySet:
        """Filter a QuerySet using the `SearchVector` and `SearchQuery` object."""
        return super().filter(qs, value)


class SearchRankFilter(AnnotatedFilter):
    """Full text search filter using the `SearchRank` object."""

    class Value(NamedTuple):
        annotation_value: SearchRank
        search_value: float

    postfix = 'search_rank'
    available_lookups = ('exact', 'gt', 'gte', 'lt', 'lte')

    def filter(self, qs: models.QuerySet, value: Value) -> models.QuerySet:
        """Filter a QuerySet using the `SearchRank` object."""
        return super().filter(qs, value)


class TrigramFilter(AnnotatedFilter):
    """Full text search filter using similarity or distance of trigram."""

    class Value(NamedTuple):
        annotation_value: Union[TrigramSimilarity, TrigramDistance]
        search_value: float

    postfix = 'trigram'
    available_lookups = ('exact', 'gt', 'gte', 'lt', 'lte')

    def filter(self, qs: models.QuerySet, value: Value) -> models.QuerySet:
        """Filter a QuerySet using similarity or distance of trigram."""
        return super().filter(qs, value)
