"""Data generation for testing."""

from datetime import datetime
from itertools import count

from django.db import connection
from django.utils.timezone import make_aware
from django_seed import Seed
from django_seed.seeder import Seeder

from .models import Task, TaskGroup, User


def generate_data() -> None:
    """Generate data for testing."""
    reset_sequences()
    seeder: Seeder = Seed.seeder()
    generate_users(seeder)
    generate_tasks(seeder)
    generate_task_groups(seeder)
    seeder.execute()
    set_task_groups_tasks()


def reset_sequences() -> None:
    """Reset database sequences."""
    with connection.cursor() as cursor:
        for model in (User, Task, TaskGroup):
            cursor.execute(f'ALTER SEQUENCE {model._meta.db_table}_id_seq RESTART WITH 1;')


def generate_users(seeder: Seeder) -> None:
    """Generate user data for testing."""
    number_generator = iter(count(1))
    seeder.add_entity(
        User, 5, {
            'birthday': datetime.strptime('01/01/2000', '%m/%d/%Y'),
            'first_name': 'Bob',
            'last_name': 'Smith',
            'is_active': False,
        },
    )
    seeder.add_entity(
        User, 10, {
            'email': lambda ie: f'alice{next(number_generator)}@domain.com',
            'first_name': 'Alice',
            'last_name': 'Stone',
            'is_active': False,
        },
    )
    seeder.add_entity(
        User, 15, {
            'email': lambda ie: f'alice{next(number_generator)}@domain.com',
            'first_name': 'Alice',
            'last_name': 'Stone',
            'is_active': True,
        },
    )
    number_generator = iter(count(1))
    seeder.add_entity(
        User, 20, {
            'email': lambda ie: f'jane_doe{next(number_generator)}@domain.com',
            'first_name': 'Jane',
            'last_name': 'Dou',
            'is_active': True,
        },
    )
    number_generator = iter(count(1))
    seeder.add_entity(
        User, 25, {
            'email': lambda ie: f'john_doe{next(number_generator)}@domain.com',
            'first_name': 'John',
            'last_name': 'Dou',
            'is_active': True,
        },
    )


def generate_tasks(seeder: Seeder) -> None:
    """Generate task data for testing."""
    seeder.add_entity(
        Task, 15, {
            'user_id': 1,
            'created_at': make_aware(datetime.strptime('01/01/2019', '%m/%d/%Y')),
            'completed_at': make_aware(datetime.strptime('02/01/2019', '%m/%d/%Y')),
        },
    )
    seeder.add_entity(
        Task, 15, {
            'user_id': 2,
            'description': 'This task is very important',
            'created_at': make_aware(datetime.strptime('01/01/2020', '%m/%d/%Y')),
            'completed_at': make_aware(datetime.strptime('02/01/2020', '%m/%d/%Y')),
        },
    )
    number_generator = iter(count(1))
    seeder.add_entity(
        Task, 45, {
            'user_id': 3,
            'name': lambda ie: f'Important task №{next(number_generator)}',
            'created_at': make_aware(datetime.strptime('01/01/2021', '%m/%d/%Y')),
            'completed_at': make_aware(datetime.strptime('02/01/2021', '%m/%d/%Y')),
        },
    )


def generate_task_groups(seeder: Seeder) -> None:
    """Generate task groups data for testing."""
    number_generator = iter(count(1))
    priority_generator = iter(count(1))
    seeder.add_entity(
        TaskGroup, 15, {
            'name': lambda ie: f'Task group №{next(number_generator)}',
            'priority': lambda ie: next(priority_generator),
        },
    )


def set_task_groups_tasks() -> None:
    """Set tasks for task groups after data generation."""
    for i, task_group in enumerate(TaskGroup.objects.all()):
        task_group.tasks.set(range(i * 5 + 1, i * 5 + 5 + 1))
