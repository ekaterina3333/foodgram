from django_filters.rest_framework import (ModelMultipleChoiceFilter,
                                           BooleanFilter, FilterSet)
from rest_framework.filters import SearchFilter

from recipes.models import Recipe, Tag


class IngredientFilter(SearchFilter):
    """Поиск по названию ингредиента."""

    search_param = 'name'


class RecipeFilter(FilterSet):
    """Фильтр для рецептов."""

    tags = ModelMultipleChoiceFilter(
        queryset=Tag.objects.all(),
        field_name='tags__slug',
        to_field_name='slug')

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
