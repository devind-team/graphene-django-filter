"""Library settings tests."""

from django.test import TestCase, override_settings
from graphene_django_filter import conf


class SettingsTests(TestCase):
    """Library settings tests."""

    def test_initial(self) -> None:
        """Test initial settings."""
        self.assertTrue(conf.settings.IS_POSTGRESQL)
        self.assertTrue(conf.settings.HAS_TRIGRAM_EXTENSION)
        self.assertEqual('filter', conf.settings.FILTER_KEY)
        self.assertEqual('and', conf.settings.AND_KEY)
        self.assertEqual('or', conf.settings.OR_KEY)
        self.assertEqual('not', conf.settings.NOT_KEY)

    def test_overridden(self) -> None:
        """Test overridden settings."""
        self.assertEqual('filter', conf.settings.FILTER_KEY)
        with override_settings(GRAPHENE_DJANGO_FILTER={'FILTER_KEY': 'where'}):
            self.assertEqual('where', conf.settings.FILTER_KEY)
        self.assertEqual('filter', conf.settings.FILTER_KEY)
