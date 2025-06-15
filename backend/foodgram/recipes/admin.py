from django.contrib import admin

from recipes.models import (Favorite, Ingredient, Recipe, IngredientInRecipe,
                            ShoppingCart, Tag)


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'slug')
    search_fields = ('name',)
    list_filter = ('name',)
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'measurement_unit')
    search_fields = ('name',)
    list_filter = ('measurement_unit',)


class IngredientInRecipe(admin.TabularInline):
    model = IngredientInRecipe
    extra = 1
    min_num = 1


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'name',
        'author',
        'cooking_time',
        'favorite_count',
    )
    search_fields = ('name', 'author__username', 'tags__name')
    list_filter = ('tags',)
    inlines = [IngredientInRecipe]

    @admin.display(description='Добавлений в избранное')
    def favorite_count(self, obj):
        """Возвращает количество добавлений рецепта в избранное."""
        return obj.favorite.count()


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ('user', 'recipe')
    search_fields = ('user__username', 'recipe__name')


@admin.register(ShoppingCart)
class ShoppingCartAdmin(admin.ModelAdmin):
    list_display = ('user', 'recipe')
    search_fields = ('user__username', 'recipe__name')
