# Graphene-Django-Filter
[![CI](https://github.com/devind-team/graphene-django-filter/workflows/CI/badge.svg)](https://github.com/devind-team/graphene-django-filter/actions) [![PyPI version](https://badge.fury.io/py/graphene-django-filter.svg)](https://badge.fury.io/py/graphene-django-filter)

This package contains advanced filters for [graphene-django](https://github.com/graphql-python/graphene-django). The standard filtering feature in graphene-django relies on the [django-filter](https://github.com/carltongibson/django-filter) library and therefore provides the flat API without the ability to use logical operators such as `and`, `or` and `not`. This library makes the API nested and adds logical expressions by extension of the `DjangoFilterConnectionField` field and the `FilterSet` class.
# Requirements
* Python (3.6, 3.7, 3.8, 3.9, 3.10)
* Graphene-Django (2.15)
# Features
## Nested API with the ability to use logical operators
To use, simply replace all `DjangoFilterConnectionField` fields with `AdvancedDjangoFilterConnectionField` fields in your queries. Also, if you create custom FilterSets, replace the inheritance from the `FilterSet` class with the inheritance from the `AdvancedFilterSet` class. For example, the following task query exposes the old flat API.
```python
import graphene
from django_filters import FilterSet
from graphene_django import DjangoObjectType
from graphene_django.filter import DjangoFilterConnectionField

class TaskFilter(FilterSet)
    class Meta:
        model = Task
        fields = {
            'name': ('exact', 'contains'),
            'user__email': ('exact', 'contains'),
            'user__first_name': ('exact', 'contains'),
            'user__last_name': ('exact', 'contains'),
        }
 
class UserType(DjangoObjectType):
    class Meta:
        model = User
        interfaces = (graphene.relay.Node,)
        fields = '__all__'
        
class TaskType(DjangoObjectType):
    user = graphene.Field(UserType)

    class Meta:
        model = Task
        interfaces = (graphene.relay.Node,)
        fields = '__all__'
        filterset_class = TaskFilter
        
class Query(graphene.ObjectType):
    tasks = DjangoFilterConnectionField(TaskType)
```
The flat API in which all filters are applied using the `and` operator looks like this.
```graphql
{
  tasks(
    name_Contains: "important"
    user_Email_Contains: "john"
    user_FirstName: "John"
    user_LastName: "Dou"
  ){
    edges {
      node {
        id
        name
      }
    }
  }
}
```
After replacing the field class with the `AdvancedDjangoFilterConnectionField` and the `FilterSet` class with the `AdvancedFilterSet` the API becomes nested with support for logical expressions.
```python
from graphene_django_filter import AdvancedDjangoFilterConnectionField, AdvancedFilterSet

class TaskFilter(AdvancedFilterSet)
    class Meta:
        model = Task
        fields = {
            'name': ('exact', 'contains'),
            'user__email': ('exact', 'contains'),
            'user__first_name': ('exact', 'contains'),
            'user__last_name': ('exact', 'contains'),
        }

class Query(graphene.ObjectType):
    tasks = AdvancedDjangoFilterConnectionField(TaskType)
```
For example, the following query returns tasks which names contain the word "important" or the user's email address contains the word "john" and the user's last name is "Dou" and the first name is not "John". Note that the operators are applied to lookups such as `contains`, `exact`, etc. at the last level of nesting.
```graphql
{
  tasks(
    filter: {
      or: [
        {name: {contains: "important"}}
        and: [
          {user: {email: {contains: "john"}}}
          {user: {lastName: {exact: "Dou"}}}
        ]
      ]
      not: {
        {user: {firstName: {exact: "John"}}}
      }
    }
  ){
    edges {
      node {
        id
        name
      }
    }
  }
}
```
The same result can be achieved with an alternative query structure because within the same object the `and` operator is always used.
```graphql
{
  tasks(
    filter: {
      or: [
        {name: {contains: "important"}}
        {
          user: {
            email: {contains: "john"}
            lastName: {exact: "Dou"}
          }
        }
      ]
      not: {
        {user: {firstName: {exact: "John"}}}
      }
    }
  ){
    edges {
      node {
        id
        name
      }
    }
  }
}
```
The filter input type has the following structure.
```graphql
input FilterInputType {
  and: [FilterInputType]
  or: [FilterInputType]
  not: FilterInputType
  ...FieldLookups
}
```
For more examples, see [tests](https://github.com/devind-team/graphene-django-filter/blob/8faa52bdfc2a66fc74a8aecb798b8358f7f7ea7c/tests/test_connection_field.py#L19).
