"""Django settings for graphene-django-filter project."""

import os
from os.path import join
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve(strict=True).parent

ENV_PATH = join(BASE_DIR, '.env')

load_dotenv(dotenv_path=ENV_PATH)

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'HOST': os.getenv('DB_HOST', 'localhost'),
        'NAME': os.getenv('DB_NAME', 'graphene_django_filter'),
        'USER': os.getenv('DB_USER', 'postgres'),
        'PASSWORD': os.getenv('DB_PASSWORD', 'postgres'),
    },
}

DEFAULT_AUTO_FIELD = 'django.db.models.AutoField'

INSTALLED_APPS = (
    'django.contrib.contenttypes',
    'django.contrib.auth',
    'django_filters',
    'django_seed',
    'graphene_django_filter',
    'tests',
)

MIDDLEWARE = []

USE_TZ = True

TIME_ZONE = 'UTC'
