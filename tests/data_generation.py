"""Data generation for testing."""

from datetime import datetime
from functools import reduce
from itertools import count, repeat

from django.utils.timezone import make_aware
from django_seed import Seed
from django_seed.seeder import Seeder

from .models import Task, TaskGroup, User


def generate_data() -> None:
    """Generate data for testing."""
    seeder: Seeder = Seed.seeder()
    generate_users(seeder)
    generate_tasks(seeder)
    generate_task_groups(seeder)
    seeder.execute()
    set_task_groups_tasks()


def generate_users(seeder: Seeder) -> None:
    """Generate user data for testing."""
    number_generator = iter(count())
    seeder.add_entity(User, 5, {'birthday': datetime.strptime('01/01/2000', '%m/%d/%Y')})
    seeder.add_entity(User, 10, {'is_active': False})
    seeder.add_entity(
        User, 15, {
            'email': lambda ie: f'john_doe{next(number_generator)}@domain.com',
        },
    )
    seeder.add_entity(User, 20, {'first_name': 'Jane'})
    seeder.add_entity(User, 25, {'last_name': 'Dou'})


def generate_tasks(seeder: Seeder) -> None:
    """Generate task data for testing."""
    seeder.add_entity(
        Task, 15, {
            'created_at': make_aware(datetime.strptime('01/01/2019', '%m/%d/%Y')),
            'completed_at': make_aware(datetime.strptime('02/01/2019', '%m/%d/%Y')),
        },
    )
    user_id_generator = iter(reduce(lambda acc, i: [*acc, *repeat(i, 5)], range(1, 6), []))
    seeder.add_entity(
        Task, 15, {
            'user_id': lambda ie: next(user_id_generator),
            'description': 'This task in very important',
            'created_at': make_aware(datetime.strptime('01/01/2020', '%m/%d/%Y')),
            'completed_at': make_aware(datetime.strptime('02/01/2020', '%m/%d/%Y')),
        },
    )
    number_generator = iter(count())
    seeder.add_entity(
        Task, 45, {
            'name': lambda ie: f'Important task №{next(number_generator)}',
            'description': 'This task in very important',
            'created_at': make_aware(datetime.strptime('01/01/2021', '%m/%d/%Y')),
            'completed_at': make_aware(datetime.strptime('02/01/2021', '%m/%d/%Y')),
        },
    )


def generate_task_groups(seeder: Seeder) -> None:
    """Generate task groups data for testing."""
    number_generator = iter(count())
    priority_generator = iter(count())
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
