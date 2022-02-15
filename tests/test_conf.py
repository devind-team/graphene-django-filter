"""Library settings tests."""

from django.test import TestCase, override_settings
from graphene_django_filter import conf


class SettingsTests(TestCase):
    """Library settings tests."""

    def test_initial(self) -> None:
        """Test initial settings."""
        self.assertTrue(conf.settings.ALLOW_FULL_TEXT_SEARCH)
        self.assertEqual('filter', conf.settings.FILTER_KEY)
        self.assertEqual('and', conf.settings.AND_KEY)
        self.assertEqual('or', conf.settings.OR_KEY)
        self.assertEqual('not', conf.settings.NOT_KEY)
        self.assertIsInstance(conf.settings.MESSAGES, dict)

    def test_overridden(self) -> None:
        """Test overridden settings."""
        self.assertEqual('filter', conf.settings.FILTER_KEY)
        with override_settings(GRAPHENE_DJANGO_FILTER={'FILTER_KEY': 'where'}):
            self.assertEqual('where', conf.settings.FILTER_KEY)
        self.assertEqual('filter', conf.settings.FILTER_KEY)
