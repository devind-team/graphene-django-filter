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

    user_fields = AdvancedDjangoFilterConnectionField(
        UserFilterFieldsType,
        description='Advanced filter fields with the `UserFilterFieldsType` type',
    )
    user_filterset = AdvancedDjangoFilterConnectionField(
        UserFilterSetClassType,
        description='Advanced filter fields with the `UserFilterSetClassType` type',
    )
    task_fields = AdvancedDjangoFilterConnectionField(
        TaskFilterFieldsType,
        description='Advanced filter field with the `TaskFilterFieldsType` type',
    )
    task_filterset = AdvancedDjangoFilterConnectionField(
        TaskFilterSetClassType,
        description='Advanced filter field with the `TaskFilterSetClassType` type',
    )
    task_group_fields = AdvancedDjangoFilterConnectionField(
        TaskGroupFilterFieldsType,
        description='Advanced filter field with the `TaskGroupFilterFieldsType` type',
    )
    task_group_filterset = AdvancedDjangoFilterConnectionField(
        TaskGroupFilterSetClassType,
        description='Advanced filter field with the `TaskGroupFilterSetClassType` type',
    )


schema = graphene.Schema(query=Query)
