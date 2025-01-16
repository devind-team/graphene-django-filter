"""Tests for additional filters for special lookups."""

from unittest.mock import patch

from django.contrib.postgres.search import SearchQuery, SearchRank, SearchVector, TrigramSimilarity
from django.db import models
from django.db.models import functions
from django.test import TestCase
from django_filters import Filter
from graphene_django_filter.filters import (
    AnnotatedFilter,
    SearchQueryFilter,
    SearchRankFilter,
    TrigramFilter,
)


from .data_generation import generate_data
from .models import User


class FiltersTests(TestCase):
    """Tests for additional filters for special lookups."""

    @classmethod
    def setUpClass(cls) -> None:
        """Set up tests for additional filters for special lookups."""
        super().setUpClass()
        generate_data()

    @patch.object(Filter, 'creation_counter', new=0)
    def test_annotate_name(self) -> None:
        """Test the `annotation_name` property of the `AnnotatedFilter` class."""
        annotated_filter = AnnotatedFilter(field_name='id', lookup_expr='exact')
        self.assertEqual('id_annotated_0_0', annotated_filter.annotation_name)

    def test_annotated_filter(self) -> None:
        """Test the `filter` method of the `AnnotatedFilter` class."""
        annotated_filter = AnnotatedFilter(field_name='id', lookup_expr='exact')
        self.assertEqual(0, annotated_filter.filter_counter)
        users = annotated_filter.filter(
            User.objects.all(),
            AnnotatedFilter.Value(
                annotation_value=functions.Concat(
                    models.Value('#'),
                    functions.Cast(models.F('id'), output_field=models.CharField()),
                ),
                search_value='#5',
            ),
        ).all()
        self.assertEqual(1, annotated_filter.filter_counter)
        self.assertEqual([5], [user.id for user in users])

    def test_search_query_filter(self) -> None:
        """Test the `SearchQueryFilter` class."""
        search_query_filter = SearchQueryFilter(field_name='first_name', lookup_expr='exact')
        users = search_query_filter.filter(
            User.objects.all(),
            SearchQueryFilter.Value(
                annotation_value=SearchVector('first_name'),
                search_value=SearchQuery('Jane'),
            ),
        ).all()
        self.assertTrue(all('Jane' in user.first_name for user in users))

    @patch.object(Filter, 'creation_counter', new=0)
    def test_search_rank_filter(self) -> None:
        """Test the `SearchQueryFilter` class."""
        search_rank_filter = SearchRankFilter(field_name='first_name', lookup_expr='lte')
        users = search_rank_filter.filter(
            User.objects.all(),
            SearchRankFilter.Value(
                annotation_value=SearchRank(
                    vector=SearchVector('first_name'),
                    query=SearchQuery('Jane'),
                ),
                search_value=1,
            ),
        ).all()
        self.assertTrue(all(hasattr(user, 'first_name_search_rank_0_0') for user in users))

    def test_trigram_filter(self) -> None:
        """Test the `TrigramFilter` class."""
        trigram_filter = TrigramFilter(field_name='field_name', lookup_expr='exact')
        users = trigram_filter.filter(
            User.objects.all(),
            TrigramFilter.Value(
                annotation_value=TrigramSimilarity('first_name', 'Jane'),
                search_value=1,
            ),
        ).all()
        self.assertTrue(all('Jane' in user.first_name for user in users))
