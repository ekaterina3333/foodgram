from django_filters.rest_framework import (AllValuesMultipleFilter,
                                           BooleanFilter, CharFilter,
                                           FilterSet)
from rest_framework.filters import SearchFilter

from recipes.models import Recipe, Tag


class IngredientFilter(SearchFilter):
    """Поиск по названию ингредиента."""

    search_param = 'name'


class RecipeFilter(FilterSet):
    """Фильтр для рецептов."""

    tags = AllValuesMultipleFilter(
        field_name='tags__slug',
        help_text='Фильтрация по слагам тегов',
    )
    is_favorited = BooleanFilter(
        method='is_recipe_in_favorites_filter'
    )
    is_in_shopping_cart = BooleanFilter(
        method='is_recipe_in_shoppingcart_filter'
    )

    class Meta:
        model = Recipe
        fields = [
            'tags',
            'author',
            'is_favorited',
            'is_in_shopping_cart'

        ]

    def is_recipe_in_favorites_filter(self, queryset, name, value):
        if value == 1:
            user = self.request.user
            return queryset.filter(favorite__user_id=user.id)
        return queryset

    def is_recipe_in_shoppingcart_filter(self, queryset, name, value):
        if value == 1:
            user = self.request.user
            return queryset.filter(shoppingcart__user_id=user.id)
        return queryset
