# Graphene-Django-Filter
[![CI](https://github.com/devind-team/graphene-django-filter/workflows/CI/badge.svg)](https://github.com/devind-team/graphene-django-filter/actions)
[![Coverage Status](https://coveralls.io/repos/github/devind-team/graphene-django-filter/badge.svg?branch=main)](https://coveralls.io/github/devind-team/graphene-django-filter?branch=main)
[![PyPI version](https://badge.fury.io/py/graphene-django-filter.svg)](https://badge.fury.io/py/graphene-django-filter)
[![License: MIT](https://img.shields.io/badge/License-MIT-success.svg)](https://opensource.org/licenses/MIT)

This package contains advanced filters for [graphene-django](https://github.com/graphql-python/graphene-django).
The standard filtering feature in graphene-django relies on the [django-filter](https://github.com/carltongibson/django-filter)
library and therefore provides the flat API without the ability to use logical operators such as
`and`, `or` and `not`. This library makes the API nested and adds logical expressions by extension
of the `DjangoFilterConnectionField` field and the `FilterSet` class.
Also, the library provides some other convenient filtering features.

# Installation
```shell
# pip
pip install graphene-django-filter
# poetry
poetry add graphene-django-filter
```

# Requirements
* Python (3.7, 3.8, 3.9, 3.10)
* Graphene-Django (2.15)

# Features

## Nested API with the ability to use logical operators
To use, simply replace all `DjangoFilterConnectionField` fields with
`AdvancedDjangoFilterConnectionField` fields in your queries.
Also,if you create custom FilterSets, replace the inheritance from the `FilterSet` class
with the inheritance from the `AdvancedFilterSet` class.
For example, the following task query exposes the old flat API.
```python
import graphene
from django_filters import FilterSet
from graphene_django import DjangoObjectType
from graphene_django.filter import DjangoFilterConnectionField

class TaskFilter(FilterSet):
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
After replacing the field class with the `AdvancedDjangoFilterConnectionField`
and the `FilterSet` class with the `AdvancedFilterSet`
the API becomes nested with support for logical expressions.
```python
import graphene
from graphene_django_filter import AdvancedDjangoFilterConnectionField, AdvancedFilterSet

class TaskFilter(AdvancedFilterSet):
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
For example, the following query returns tasks which names contain the word "important"
or the user's email address contains the word "john" and the user's last name is "Dou"
and the first name is not "John".
Note that the operators are applied to lookups
such as `contains`, `exact`, etc. at the last level of nesting.
```graphql
{
  tasks(
    filter: {
      or: [
        {name: {contains: "important"}}
        {
            and: [
              {user: {email: {contains: "john"}}}
              {user: {lastName: {exact: "Dou"}}}
            ]
        }
      ]
      not: {
        user: {firstName: {exact: "John"}}
      }
    }
  ) {
    edges {
      node {
        id
        name
      }
    }
  }
}
```
The same result can be achieved with an alternative query structure
because within the same object the `and` operator is always used.
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
        user: {firstName: {exact: "John"}}
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
For more examples, see [tests](https://github.com/devind-team/graphene-django-filter/blob/06ed0af8def8a4378b4c65a5d137ef17b6176cab/tests/test_queries_execution.py#L23).

## Full text search
Django provides the [API](https://docs.djangoproject.com/en/3.2/ref/contrib/postgres/search/)
for PostgreSQL full text search. Graphene-Django-Filter inject this API into the GraphQL filter API.
To use, add `full_text_search` lookup to fields for which you want to enable full text search.
For example, the following type has full text search for
`first_name` and `last_name` fields.
```python
import graphene
from graphene_django import DjangoObjectType
from graphene_django_filter import AdvancedDjangoFilterConnectionField

class UserType(DjangoObjectType):
    class Meta:
        model = User
        interfaces = (graphene.relay.Node,)
        fields = '__all__'
        filter_fields = {
            'email': ('exact', 'startswith', 'contains'),
            'first_name': ('exact', 'contains', 'full_text_search'),
            'last_name': ('exact', 'contains', 'full_text_search'),
        }

class Query(graphene.ObjectType):
    users = AdvancedDjangoFilterConnectionField(UserType)
```
Since this feature belongs to the AdvancedFilterSet,
it can be used in a custom FilterSet.
The following example will work exactly like the previous one.
```python
import graphene
from graphene_django import DjangoObjectType
from graphene_django_filter import AdvancedDjangoFilterConnectionField, AdvancedFilterSet

class UserFilter(AdvancedFilterSet):
    class Meta:
        model = User
        fields = {
            'email': ('exact', 'startswith', 'contains'),
            'first_name': ('exact', 'contains', 'full_text_search'),
            'last_name': ('exact', 'contains', 'full_text_search'),
        }

class UserType(DjangoObjectType):
    class Meta:
        model = User
        interfaces = (graphene.relay.Node,)
        fields = '__all__'
        filterset_class = UserFilter

class Query(graphene.ObjectType):
    users = AdvancedDjangoFilterConnectionField(UserType)
```
Full text search API includes SearchQuery, SearchRank, and Trigram filters.
SearchQuery and SearchRank filters are at the top level.
If some field has been enabled for full text search then it can be included in the field array.
The following queries show an example of using the SearchQuery and SearchRank filters.
```graphql
{
  users(
    filter: {
      searchQuery: {
        vector: {
          fields: ["first_name"]
        }
        query: {
          or: [
            {value: "Bob"}
            {value: "Alice"}
          ]
        }
      }
    }
  ){
    edges {
      node {
        id
        firstName
        lastName  
      }
    }
  }
}
```
```graphql
{
  users(
    filter: {
      searchRank: {
        vector: {fields: ["first_name", "last_name"]}
        query: {value: "John Dou"}
        lookups: {gte: 0.5}
      }
    }
  ){
    edges {
      node {
        id
        firstName
        lastName  
      }
    }
  }
}
```
Trigram filter belongs to the corresponding field.
The following query shows an example of using the Trigram filter.
```graphql
{
  users(
    filter: {
      firstName: {
        trigram: {
          value: "john"
          lookups: {gte: 0.85}
        }
      }
    }
  ){
    edges {
      node {
        id
        firstName
        lastName  
      }
    }
  }
}
```
Input types have the following structure.
```graphql
input SearchConfigInputType {
  value: String!
  isField: Boolean
}
enum SearchVectorWeight {
  A
  B
  C
  D
}
input SearchVectorInputType {
  fields: [String!]!
  config: SearchConfigInputType
  weight: SearchVectorWeight
}
enum SearchQueryType {
  PLAIN
  PHRASE
  RAW
  WEBSEARCH
}
input SearchQueryInputType {
  value: String
  config: SearchConfigInputType
  and: [SearchQueryInputType]
  or: [SearchQueryInputType]
  not: SearchQueryInputType
}
input SearchQueryFilterInputType {
  vector: SearchVectorInputType!
  query: SearchQueryInputType!
}
input FloatLookupsInputType {
  exact: Float
  gt: Float
  gte: Float
  lt: Float
  lte: Float
}
input SearchRankWeightsInputType {
  D: Float
  C: Float
  B: Float
  A: Float
}
input SearchRankFilterInputType {
  vector: SearchVectorInputType!
  query: SearchQueryInputType!
  lookups: FloatLookupsInputType!
  weights: SearchRankWeightsInputType
  coverDensity: Boolean
  normalization: Int
}
enum TrigramSearchKind {
  SIMILARITY
  DISTANCE
}
input TrigramFilterInputType {
  kind: TrigramSearchKind
  lookups: FloatLookupsInputType!
  value: String!
}
```
For more examples, see [tests](https://github.com/devind-team/graphene-django-filter/blob/06ed0af8def8a4378b4c65a5d137ef17b6176cab/tests/test_queries_execution.py#L134).

## Settings
The library can be customised using settings.
To add settings, create a dictionary
with name `GRAPHENE_DJANGO_FILTER` in the project’s `settings.py`.
The default settings are as follows.
```python
GRAPHENE_DJANGO_FILTER = {
    'FILTER_KEY': 'filter',
    'AND_KEY': 'and',
    'OR_KEY': 'or',
    'NOT_KEY': 'not',
}
```
To read the settings, import them from the `conf` module.
```python
from graphene_django_filter.conf import settings

print(settings.FILTER_KEY)
```
The `settings` object also includes fixed settings, which depend on the user's environment.
`IS_POSTGRESQL` determinate that current database is PostgreSQL
and `HAS_TRIGRAM_EXTENSION` that `pg_trgm` extension is installed.
