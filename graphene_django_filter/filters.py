"""Additional filters for special lookups."""

from typing import Any, NamedTuple, Union

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
        annotate_value: Any
        search_value: Any

    postfix = 'annotated'

    @property
    def annotate_name(self) -> str:
        """Return the name used for the annotation."""
        return f'{self.field_name}_{self.postfix}_{self.creation_counter}'

    def filter(self, qs: models.QuerySet, value: Value) -> models.QuerySet:
        """Filter a QuerySet using annotation."""
        if value in EMPTY_VALUES:
            return qs
        if self.distinct:
            qs = qs.distinct()
        qs = qs.annotate(**{self.annotate_name: value.annotate_value})
        lookup = f'{self.annotate_name}{LOOKUP_SEP}{self.lookup_expr}'
        return self.get_method(qs)(**{lookup: value.search_value})


class SearchQueryFilter(AnnotatedFilter):
    """Full text search filter using the SearchVector and SearchQuery object."""

    class Value(NamedTuple):
        annotate_value: SearchVector
        search_value: SearchQuery

    postfix = 'search_query'

    def filter(self, qs: models.QuerySet, value: Value) -> models.QuerySet:
        """Filter a QuerySet using the SearchVector and SearchQuery object."""
        return super().filter(qs, value)


class SearchRankFilter(AnnotatedFilter):
    """Full text search filter using the SearchRank object."""

    class Value(NamedTuple):
        annotate_value: SearchRank
        search_value: float

    postfix = 'search_rank'

    def filter(self, qs: models.QuerySet, value: Value) -> models.QuerySet:
        """Filter a QuerySet using the SearchRank object."""
        return super().filter(qs, value)


class TrigramFilter(AnnotatedFilter):
    """Full text search filter using similarity or distance of trigram."""

    class Value(NamedTuple):
        annotate_value: Union[TrigramSimilarity, TrigramDistance]
        search_value: float

    posix = 'trigram'

    def filter(self, qs: models.QuerySet, value: Value) -> models.QuerySet:
        """Filter a QuerySet using similarity or distance of trigram."""
        return super().filter(qs, value)
