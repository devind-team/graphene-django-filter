"""Library settings."""

from typing import Any, Optional

from django.conf import settings as django_settings
from django.db import connection
from django.test.signals import setting_changed
from django.utils.translation import gettext_lazy as _

FIXED_SETTINGS = {
    'ALLOW_FULL_TEXT_SEARCH': connection.vendor == 'postgresql',
}
DEFAULT_SETTINGS = {
    'FILTER_KEY': 'filter',
    'AND_KEY': 'and',
    'OR_KEY': 'or',
    'NOT_KEY': 'not',
    'MESSAGES': {
        'FILTER_DESCRIPTION': _('FILTER_DESCRIPTION'),
        'AND_DESCRIPTION': _('AND_DESCRIPTION'),
        'OR_DESCRIPTION': _('OR_DESCRIPTION'),
        'NOT_DESCRIPTION': _('NOT_DESCRIPTION'),
        'FIELD_DESCRIPTION': _('FIELD_DESCRIPTION'),
        'SUBFIELD_DESCRIPTION': _('SUBFIELD_DESCRIPTION'),
        'LOOKUP_DESCRIPTION': _('LOOKUP_DESCRIPTION'),
    },
}
DJANGO_SETTINGS_KEY = 'GRAPHENE_DJANGO_FILTER'


class Settings:
    """Library settings.

    Settings consist of fixed ones that depend on the user environment
    and others that can be set with Django settings.py module.
    """

    def __init__(self, user_settings: Optional[dict] = None) -> None:
        self._user_settings = user_settings

    @property
    def user_settings(self) -> dict:
        """Return user-defined settings."""
        if self._user_settings is None:
            self._user_settings = getattr(django_settings, DJANGO_SETTINGS_KEY, {})
        return self._user_settings

    def __getattr__(self, name: str) -> str:
        """Return a setting value."""
        if name not in FIXED_SETTINGS and name not in DEFAULT_SETTINGS:
            raise AttributeError(f'Invalid Graphene setting: `{name}`')
        if name in self.user_settings:
            return self.user_settings[name]
        elif name in FIXED_SETTINGS:
            return FIXED_SETTINGS[name]
        else:
            return DEFAULT_SETTINGS[name]


settings = Settings(None)


def reload_settings(setting: str, value: Any, **kwargs) -> None:
    """Reload settings in response to the `setting_changed` signal."""
    global settings
    if setting == DJANGO_SETTINGS_KEY:
        settings = Settings(value)


setting_changed.connect(reload_settings)
