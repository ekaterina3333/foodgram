from django.db.models import Sum
from django.http import HttpResponse
from rest_framework.permissions import (
    AllowAny, IsAuthenticatedOrReadOnly, IsAuthenticated
)
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.decorators import action
from rest_framework.pagination import LimitOffsetPagination
from rest_framework import viewsets, status
from django.urls import reverse

from rest_framework.viewsets import ModelViewSet
from djoser.views import UserViewSet
from rest_framework.response import Response

from .pagination import CustomPagination
from .permissions import IsAuthorOrReadOnly
from recipes.models import (Ingredient, Tag, Recipe, Follow,
                            IngredientInRecipe, ShoppingCart, Favorite)

from .serializers import (IngredientSerializer, TagSerializer,
                          UserProfileSerializer, AvatarSerializer,
                          RecipeSerializer, FollowSerializer,
                          CreateRecipeSerializer, AddFavoritesSerializer)
from users.models import User
from .filters import IngredientFilter, RecipeFilter


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    """Вьюсет для работы с обьектами класса Ingredient."""

    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = (AllowAny,)
    filter_backends = (IngredientFilter,)
    search_fields = ('^name',)


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = (AllowAny,)


class UserViewSet(UserViewSet):
    """Вьюсет для работы с обьектами класса User и подписки на авторов."""

    queryset = User.objects.all()
    serializer_class = UserProfileSerializer
    permission_classes = (IsAuthenticatedOrReadOnly,)
    pagination_class = LimitOffsetPagination

    @action(
        detail=False,
        methods=('get',),
        permission_classes=(IsAuthenticated, ),
        url_path='subscriptions',
        url_name='subscriptions',
    )
    def subscriptions(self, request):
        """Метод для создания страницы подписок"""

        queryset = User.objects.filter(follow__user=request.user)
        pages = self.paginate_queryset(queryset)
        serializer = FollowSerializer(pages, many=True,
                                      context={'request': request})
        return self.get_paginated_response(serializer.data)

    @action(
        detail=True,
        methods=('post', 'delete'),
        permission_classes=(IsAuthenticated,),
        url_path='subscribe',
        url_name='subscribe',
    )
    def subscribe(self, request, id):
        """Метод для управления подписками """

        user = request.user
        author = get_object_or_404(User, id=id)
        serializer = FollowSerializer(
            author,
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        if request.method == 'POST':
            Follow.objects.create(user=user, author=author)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        elif request.method == 'DELETE':
            Follow.objects.filter(user=user, author=author).delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=['PUT', 'DELETE'], url_path='me/avatar')
    def update_avatar(self, request):
        user = request.user
        if request.method == 'DELETE':
            if user.avatar:
                user.avatar.delete(save=False)
                user.avatar = None
                user.save()
                return Response({"detail": "Аватар успешно удален"},
                                status=204)
            return Response({"detail": "Аватар не удален"},
                            status=400)

        serializer = AvatarSerializer(user, data=request.data)
        if not serializer.is_valid(raise_exception=True):
            return Response(serializer.errors, status=400)
        serializer.save()
        return Response(serializer.data)


class RecipeViewSet(ModelViewSet):
    """ViewSet для обработки запросов, связанных с рецептами."""

    queryset = Recipe.objects.all()
    pagination_class = CustomPagination
    permission_classes = (IsAuthorOrReadOnly,)
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter

    def get_serializer_class(self):
        """Метод для вызова определенного сериализатора. """

        if self.action in ('list', 'retrieve', 'favorite', 'shopping_cart'):
            return RecipeSerializer
        elif self.action in ('create', 'partial_update'):
            return CreateRecipeSerializer

    def get_serializer_context(self):
        """Метод для передачи контекста. """

        context = super().get_serializer_context()
        context.update({'request': self.request})
        return context

    def _manage_recipe_relation(self, request, pk,
                                relation_model):
        """Общий метод для управления связями рецептов."""
        user = request.user
        recipe = get_object_or_404(Recipe, id=pk)
        serializer = self.get_serializer(recipe)
        if request.method == 'POST':
            if relation_model.__name__ == 'Favorite':
                serializer.validate_recipe_in_favorite(recipe, user)
            else:
                serializer.validate_recipe_in_cart(recipe, user)

            relation_model.objects.create(user=user, recipe=recipe)
            return Response(serializer.data,
                            status=status.HTTP_201_CREATED)

        if request.method == 'DELETE':
            if relation_model.__name__ == 'Favorite':
                serializer.validate_recipe_not_in_favorite(recipe, user)
            else:
                serializer.validate_recipe_not_in_cart(recipe, user)

            relation_model.objects.filter(user=user, recipe=recipe).delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=True,
        methods=('post', 'delete'),
        permission_classes=(IsAuthenticated,),
        url_path='favorite',
        url_name='favorite',
    )
    def favorite(self, request, pk):
        """Метод для управления избранными рецептами."""
        return self._manage_recipe_relation(
            request, pk, Favorite
        )

    @action(
        detail=True,
        methods=('post', 'delete'),
        permission_classes=(IsAuthenticated,),
        url_path='shopping_cart',
        url_name='shopping_cart',
    )
    def shopping_cart(self, request, pk):
        """Метод для управления списком покупок."""
        return self._manage_recipe_relation(
            request, pk, ShoppingCart
        )

    @staticmethod
    def ingredients_to_txt(ingredients):
        """Метод для объединения ингредиентов в список для загрузки"""

        shopping_list = ''
        for ingredient in ingredients:
            shopping_list += (
                f"{ingredient['ingredient__name']}  - "
                f"{ingredient['sum']}"
                f"({ingredient['ingredient__measurement_unit']})\n"
            )
        return shopping_list

    @action(
        detail=False,
        methods=('get',),
        permission_classes=(IsAuthenticated,),
        url_path='download_shopping_cart',
        url_name='download_shopping_cart',
    )
    def download_shopping_cart(self, request):
        """Метод для загрузки ингредиентов и их количества
         для выбранных рецептов"""

        ingredients = IngredientInRecipe.objects.filter(
            recipe__shoppingcart__user=request.user
        ).values(
            'ingredient__name',
            'ingredient__measurement_unit'
        ).annotate(sum=Sum('amount'))
        shopping_list = self.ingredients_to_txt(ingredients)
        return HttpResponse(shopping_list, content_type='text/plain')

    @action(
        detail=True, methods=['get'], url_path='get-link'
    )
    def get_short_link(self, request, pk=None):
        recipe = get_object_or_404(Recipe, id=pk)
        short_code = recipe.short_code
        short_link = f"https://{request.get_host()}/s/{short_code}"
        return Response({'short-link': short_link}, status=status.HTTP_200_OK)
