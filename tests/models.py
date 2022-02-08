"""Django models for testing."""

from django.db import models


class User(models.Model):
    """User model."""

    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=128)
    last_name = models.CharField(max_length=128)
    is_active = models.BooleanField(default=True)
    birthday = models.DateField(null=True)


class Task(models.Model):
    """Task model."""

    name = models.CharField(max_length=256)
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True)
    description = models.TextField()

    user = models.ForeignKey(User, on_delete=models.CASCADE)


class TaskGroup(models.Model):
    """Task group model."""

    name = models.CharField(max_length=256)
    priority = models.PositiveSmallIntegerField(default=0)
    tasks = models.ManyToManyField(Task)
