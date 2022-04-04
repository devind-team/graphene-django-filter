"""GraphQL schema."""

import graphene
from graphene_django_filter import AdvancedDjangoFilterConnectionField

from .object_types import (
    TaskFilterFieldsType,
    TaskFilterSetClassType,
    TaskGroupFilterFieldsType,
    TaskGroupFilterSetClassType,
    UserFilterFieldsType,
    UserFilterSetClassType,
)


class Query(graphene.ObjectType):
    """Schema queries."""

    users_fields = AdvancedDjangoFilterConnectionField(
        UserFilterFieldsType,
        description='Advanced filter fields with the `UserFilterFieldsType` type',
    )
    users_filterset = AdvancedDjangoFilterConnectionField(
        UserFilterSetClassType,
        filter_input_type_prefix='UserFilterSetClass',
        description='Advanced filter fields with the `UserFilterSetClassType` type',
    )
    tasks_fields = AdvancedDjangoFilterConnectionField(
        TaskFilterFieldsType,
        description='Advanced filter field with the `TaskFilterFieldsType` type',
    )
    tasks_filterset = AdvancedDjangoFilterConnectionField(
        TaskFilterSetClassType,
        filter_input_type_prefix='TaskFilterSetClass',
        description='Advanced filter field with the `TaskFilterSetClassType` type',
    )
    task_groups_fields = AdvancedDjangoFilterConnectionField(
        TaskGroupFilterFieldsType,
        description='Advanced filter field with the `TaskGroupFilterFieldsType` type',
    )
    task_groups_filterset = AdvancedDjangoFilterConnectionField(
        TaskGroupFilterSetClassType,
        filter_input_type_prefix='TaskGroupFilterSetClass',
        description='Advanced filter field with the `TaskGroupFilterSetClassType` type',
    )


schema = graphene.Schema(query=Query)
