"""DjangoFilterConnectionField module.

Use DjangoFilterConnectionField class from this
module instead of graphene_django one.
"""

from graphene_django import DjangoConnectionField


class DjangoFilterConnectionField(DjangoConnectionField):
    """Allow to use advanced filters provided by this library."""

    pass
