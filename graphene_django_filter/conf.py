"""Library settings."""

from typing import Any, Dict, Optional, Union

from django.conf import settings as django_settings
from django.db import connection
from django.test.signals import setting_changed


def get_fixed_settings() -> Dict[str, bool]:
    """Return fixed settings."""
    is_postgresql = connection.vendor == 'postgresql'
    has_trigram_extension = False
    if is_postgresql:
        with connection.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM pg_available_extensions WHERE name='pg_trgm'")
            has_trigram_extension = cursor.fetchone()[0] == 1
    return {
        'IS_POSTGRESQL': is_postgresql,
        'HAS_TRIGRAM_EXTENSION': has_trigram_extension,
    }


FIXED_SETTINGS = get_fixed_settings()
DEFAULT_SETTINGS = {
    'FILTER_KEY': 'filter',
    'AND_KEY': 'and',
    'OR_KEY': 'or',
    'NOT_KEY': 'not',
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

    def __getattr__(self, name: str) -> Union[str, bool]:
        """Return a setting value."""
        if name not in FIXED_SETTINGS and name not in DEFAULT_SETTINGS:
            raise AttributeError(f'Invalid Graphene setting: `{name}`')
        if name in FIXED_SETTINGS:
            return FIXED_SETTINGS[name]
        elif name in self.user_settings:
            return self.user_settings[name]
        else:
            return DEFAULT_SETTINGS[name]


settings = Settings(None)


def reload_settings(setting: str, value: Any, **kwargs) -> None:
    """Reload settings in response to the `setting_changed` signal."""
    global settings
    if setting == DJANGO_SETTINGS_KEY:
        settings = Settings(value)


setting_changed.connect(reload_settings)
