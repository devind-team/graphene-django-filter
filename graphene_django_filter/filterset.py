"""`AdvancedFilterSet` class module.

Use the `AdvancedFilterSet` class from this module instead of the `FilterSet` from django-filter.
"""

from typing import Any, Dict, List, Optional, Type, Union, cast

from django.db import models
from django.db.models.constants import LOOKUP_SEP
from django.forms import Form
from django.forms.utils import ErrorDict
from django_filters import Filter
from django_filters.conf import settings
from django_filters.filterset import BaseFilterSet, FilterSetMetaclass
from graphene.types.inputobjecttype import InputObjectTypeContainer
from wrapt import ObjectProxy


def tree_input_type_to_data(
    tree_input_type: InputObjectTypeContainer,
    prefix: str = '',
) -> Dict[str, Any]:
    """Convert a tree_input_type to a FilterSet data."""
    result: Dict[str, Any] = {}
    for key, value in tree_input_type.items():
        if key in ('and', 'or'):
            result[key] = [tree_input_type_to_data(subtree) for subtree in value]
        elif key == 'not':
            result[key] = tree_input_type_to_data(value)
        else:
            k = (prefix + LOOKUP_SEP + key if prefix else key).replace(
                LOOKUP_SEP + settings.DEFAULT_LOOKUP_EXPR, '',
            )
            if isinstance(value, InputObjectTypeContainer):
                result.update(tree_input_type_to_data(value, k))
            else:
                result[k] = value
    return result


class QuerySetProxy(ObjectProxy):
    """Proxy for a QuerySet object.

    The Django-filter library works with QuerySet objects,
    but such objects do not provide the ability to apply the negation operator to the entire object.
    Therefore, it is convenient to work with the Q object instead of the QuerySet.
    This class replaces the original QuerySet object,
    and creates a Q object when calling the `filter` and `exclude` methods.
    """

    __slots__ = 'q'

    def __init__(self, wrapped: models.QuerySet) -> None:
        super().__init__(wrapped)
        self.q = models.Q()

    def __getattr__(self, name: str) -> Any:
        """Return QuerySet attributes for all cases except `filter` and `exclude`."""
        if name == 'filter':
            return self.filter_
        elif name == 'exclude':
            return self.exclude_
        return super().__getattr__(name)

    def filter_(self, *args, **kwargs) -> 'QuerySetProxy':
        """Replace the `filter` method of the QuerySet class."""
        if len(kwargs) == 0 and len(args) == 1 and isinstance(args[0], models.Q):
            q = args[0]
        else:
            q = models.Q(*args, **kwargs)
        self.q = self.q & q
        return self

    def exclude_(self, *args, **kwargs) -> 'QuerySetProxy':
        """Replace the `exclude` method of the QuerySet class."""
        if len(kwargs) == 0 and len(args) == 1 and isinstance(args[0], models.Q):
            q = args[0]
        else:
            q = models.Q(*args, **kwargs)
        self.q = self.q & ~q
        return self


def get_q(queryset: models.QuerySet, filter_obj: Filter, value: Any) -> models.Q:
    """Return a Q object for a queryset, filter and value."""
    queryset_proxy = QuerySetProxy(queryset)
    filter_obj.filter(queryset_proxy, value)
    return queryset_proxy.q


class AdvancedFilterSet(BaseFilterSet, metaclass=FilterSetMetaclass):
    """Allow you to use advanced filters with `or` and `and` expressions."""

    class TreeFormMixin(Form):
        """Tree-like form mixin."""

        def __init__(
            self,
            and_forms: Optional[List['AdvancedFilterSet.TreeFormMixin']] = None,
            or_forms: Optional[List['AdvancedFilterSet.TreeFormMixin']] = None,
            not_form: Optional['AdvancedFilterSet.TreeFormMixin'] = None,
            *args,
            **kwargs
        ) -> None:
            super().__init__(*args, **kwargs)
            self.and_forms = and_forms or []
            self.or_forms = or_forms or []
            self.not_form = not_form

        @property
        def errors(self) -> ErrorDict:
            """Return an ErrorDict for the data provided for the form."""
            self_errors: ErrorDict = super().errors
            for key in ('and', 'or'):
                errors: ErrorDict = ErrorDict()
                for i, form in enumerate(getattr(self, f'{key}_forms')):
                    if form.errors:
                        errors[f'{key}_{i}'] = form.errors
                if len(errors):
                    self_errors.update({key: errors})
            if self.not_form and self.not_form.errors:
                self_errors.update({'not': self.not_form.errors})
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
            data={k: v for k, v in data.items() if k not in ('and', 'or', 'not')},
            and_forms=[self.create_form(form_class, and_data) for and_data in data.get('and', [])],
            or_forms=[self.create_form(form_class, or_data) for or_data in data.get('or', [])],
            not_form=self.create_form(form_class, data['not']) if data.get('not', None) else None,
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

    def filter_queryset(self, queryset: models.QuerySet) -> models.QuerySet:
        """Filter a queryset with a top level form's `cleaned_data`."""
        return queryset.filter(self.get_q_for_form(queryset, self.form))

    def get_q_for_form(
        self,
        queryset: models.QuerySet,
        form: Union[Form, TreeFormMixin],
    ) -> models.Q:
        """Return a Q object for a form's `cleaned_data` using `and`, `or` or `not` operator."""
        q = models.Q()
        for name, value in form.cleaned_data.items():
            q = q & get_q(queryset, self.find_filter(name), value)
        and_q = models.Q()
        for and_form in form.and_forms:
            and_q = and_q & self.get_q_for_form(queryset, and_form)
        or_q = models.Q()
        for or_form in form.or_forms:
            or_q = or_q | self.get_q_for_form(queryset, or_form)
        not_q = ~self.get_q_for_form(queryset, form.not_form) if form.not_form else models.Q()
        return q & and_q & or_q & not_q
