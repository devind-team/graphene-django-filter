"""Django settings for graphene-django-filter project."""

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    },
}

INSTALLED_APPS = (
    'django.contrib.contenttypes',
    'django.contrib.auth',
    'tests',
)

MIDDLEWARE = []

TIME_ZONE = 'UTC'
