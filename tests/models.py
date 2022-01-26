"""Django models for testing."""

from django.db import models


class User(models.Model):
    """User model."""

    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=128)
    last_name = models.CharField(max_length=128)
    sir_name = models.CharField(max_length=128)
    is_active = models.BooleanField(default=True)
    birthday = models.DateField(null=True)


class Task(models.Model):
    """Task model."""

    name = models.CharField(max_length=256)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
