"""`AdvancedFilterSet` class module.

Use the `AdvancedFilterSet` class from this module instead of the `FilterSet` from django-filter.
"""

from typing import Any, Dict, Optional, Type, Union, cast

from django.db.models.constants import LOOKUP_SEP
from django.forms import Form
from django.forms.utils import ErrorDict
from django_filters import Filter
from django_filters.conf import settings
from django_filters.filterset import BaseFilterSet, FilterSetMetaclass
from graphene.types.inputobjecttype import InputObjectTypeContainer


def tree_input_type_to_data(
    tree_input_type: InputObjectTypeContainer,
    prefix: str = '',
) -> Dict[str, Any]:
    """Convert a tree_input_type to a FilterSet data."""
    result: Dict[str, Any] = {}
    for key, value in tree_input_type.items():
        if key in ('and', 'or'):
            result[key] = tree_input_type_to_data(value)
        else:
            k = prefix + LOOKUP_SEP + key if prefix else key
            if isinstance(value, InputObjectTypeContainer):
                result.update(tree_input_type_to_data(value, k))
            else:
                result[k] = value
    return result


class AdvancedFilterSet(BaseFilterSet, metaclass=FilterSetMetaclass):
    """Allow you to use advanced filters with `or` and `and` expressions."""

    class TreeFormMixin(Form):
        """Tree-like form mixin."""

        def __init__(
            self,
            or_form: Optional['AdvancedFilterSet.TreeFormMixin'] = None,
            and_form: Optional['AdvancedFilterSet.TreeFormMixin'] = None,
            *args,
            **kwargs
        ) -> None:
            super().__init__(*args, **kwargs)
            self.or_form = or_form
            self.and_form = and_form

        @property
        def errors(self) -> ErrorDict:
            """Return an ErrorDict for the data provided for the form."""
            self_errors: ErrorDict = super().errors
            if self.and_form:
                self_errors.update({'and': self.and_form.errors})
            if self.or_form:
                self_errors.update({'or': self.or_form.errors})
            return self_errors

    def get_form_class(self) -> Type[Union[Form, TreeFormMixin]]:
        """Return a django Form class suitable of validating the filterset data.

        The form must be tree-like because the data is tree-like.
        """
        form_class = super(AdvancedFilterSet, self).get_form_class()
        tree_form = cast(
            Type[Union[Form, AdvancedFilterSet.TreeFormMixin]],
            type(
                f'{form_class.__name__.replace("Form", "")}TreeForm',
                (form_class, AdvancedFilterSet.TreeFormMixin),
                {},
            ),

        )
        return tree_form

    @property
    def form(self) -> Union[Form, TreeFormMixin]:
        """Return a django Form suitable of validating the filterset data."""
        if not hasattr(self, '_form'):
            form_class = self.get_form_class()
            if self.is_bound:
                self._form = self.create_form(form_class, self.data)
            else:
                self._form = form_class(prefix=self.form_prefix)
        return self._form

    def create_form(
        self,
        form_class: Type[Union[Form, TreeFormMixin]],
        data: Dict[str, Any],
    ) -> Union[Form, TreeFormMixin]:
        """Create a form from a form class and data."""
        return form_class(
            data={k: v for k, v in data.items() if k not in ('or', 'and')},
            or_form=self.create_form(form_class, data['or']) if data.get('or', None) else None,
            and_form=self.create_form(form_class, data['and']) if data.get('and', None) else None,
        )

    def find_filter(self, data_key: str) -> Filter:
        """Find a filter using a data key.

        The data key may differ from a filter name, because
        the data keys may contain DEFAULT_LOOKUP_EXPR and user can create
        a AdvancedFilterSet class without following the naming convention.
        """
        if LOOKUP_SEP in data_key:
            field_name, lookup_expr = data_key.rsplit(LOOKUP_SEP, 1)
        else:
            field_name, lookup_expr = data_key, settings.DEFAULT_LOOKUP_EXPR
        key = field_name if lookup_expr == settings.DEFAULT_LOOKUP_EXPR else data_key
        if key in self.filters:
            return self.filters[key]
        for filter_value in self.filters.values():
            if filter_value.field_name == field_name and filter_value.lookup_expr == lookup_expr:
                return filter_value
