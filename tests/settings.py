"""Django settings for graphene-django-filter project."""

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    },
}

DEFAULT_AUTO_FIELD = 'django.db.models.AutoField'

INSTALLED_APPS = (
    'django.contrib.contenttypes',
    'django.contrib.auth',
    'django_filters',
    'tests',
)

MIDDLEWARE = []

USE_TZ = True

TIME_ZONE = 'UTC'
