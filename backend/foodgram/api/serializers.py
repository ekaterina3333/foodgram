from rest_framework import serializers
from rest_framework.serializers import ModelSerializer
from django.core.exceptions import ValidationError
from drf_extra_fields.fields import Base64ImageField
from recipes.models import (Ingredient, Tag, TagInRecipe, Follow,
                            IngredientInRecipe, Recipe, Favorite, ShoppingCart)

from users.models import User


class IngredientSerializer(ModelSerializer):
    """Сериализатор для ингредиентов."""

    class Meta:

        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class RecipeMiniSerializer(serializers.ModelSerializer):
    """
    Базовый сериализатор рецепта.
    """
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class TagSerializer(ModelSerializer):
    """Сериализатор для тэгов."""

    class Meta:

        model = Tag
        fields = ('id', 'name', 'slug')


class UserProfileSerializer(serializers.ModelSerializer):
    """Сериализатор для модели User."""

    is_subscribed = serializers.SerializerMethodField()
    avatar = serializers.SerializerMethodField()

    class Meta:

        model = User
        fields = ('email', 'id', 'username', 'first_name', 'last_name',
                  'is_subscribed', 'avatar')

    def get_is_subscribed(self, obj):
        """Метод проверки подписки"""

        user = self.context.get('request').user
        if user.is_anonymous:
            return False
        return Follow.objects.filter(user=user, author=obj.id).exists()

    def get_avatar(self, obj):
        return obj.avatar.url if obj.avatar else None

    def get_subscribe(self, obj):
        """Метод для валидации подписки/отписки"""
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return None

        data = {
            'user': request.user.id,
            'author': obj.id
        }

        if request.method == 'POST':
            if request.user == obj:
                raise serializers.ValidationError(
                    {"error": "Нельзя подписаться на самого себя"}
                )

            if Follow.objects.filter(**data).exists():
                raise serializers.ValidationError(
                    {"error": "Вы уже подписаны на этого пользователя"}
                )

        elif request.method == 'DELETE':
            if not Follow.objects.filter(**data).exists():
                raise serializers.ValidationError(
                    {"error": "Вы не подписаны на этого пользователя"}
                )

        return None


class AvatarSerializer(serializers.ModelSerializer):
    """Сериализатор аватара."""

    avatar = Base64ImageField(required=True)

    class Meta:
        model = User
        fields = ('avatar',)

    def to_representation(self, instance):
        return {
            'avatar': instance.avatar.url
            if instance.avatar else None
        }

    def update(self, instance, validated_data):
        """Обновление аватара с автоматическим удалением старого."""
        old_avatar = instance.avatar
        instance.avatar = validated_data['avatar']
        instance.save()

        if old_avatar and old_avatar != instance.avatar:
            old_avatar.delete(save=False)

        return instance


class AdditionalForRecipeSerializer(serializers.ModelSerializer):
    """Дополнительный сериализатор для рецептов """

    class Meta:
        """Мета-параметры сериализатора"""

        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class FollowSerializer(UserProfileSerializer):
    """Сериализатор для модели Follow."""

    recipes = serializers.SerializerMethodField(
        read_only=True,
        method_name='get_recipes')
    recipes_count = serializers.SerializerMethodField(
        read_only=True
    )
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        """Мета-параметры сериализатора"""

        model = User
        fields = UserProfileSerializer.Meta.fields + ('recipes',
                                                      'recipes_count')
        read_only_fields = ('email', 'username', 'first_name', 'last_name')

    def validate(self, data):
        """
        Валидация для подписки/отписки
        """
        request = self.context.get('request')
        author = self.instance

        if not request or not request.user.is_authenticated:
            raise ValidationError("Требуется авторизация")

        if request.method == 'POST':
            self._validate_subscription(author, request.user)
        elif request.method == 'DELETE':
            self._validate_unsubscription(author, request.user)

        return data

    def _validate_subscription(self, author, user):
        if user == author:
            raise ValidationError(
                {"error": "Нельзя подписаться на самого себя"}
            )
        if Follow.objects.filter(user=user, author=author).exists():
            raise ValidationError(
                {"error": "Вы уже подписаны на этого пользователя"}
            )

    def _validate_unsubscription(self, author, user):
        if not Follow.objects.filter(user=user, author=author).exists():
            raise ValidationError(
                {"error": "Вы не подписаны на этого пользователя"}
            )

    def get_recipes(self, obj):
        """Метод для получения рецептов"""
        request = self.context.get('request')
        recipes = obj.recipes.all()
        recipes_limit = request.query_params.get('recipes_limit')
        if recipes_limit:
            recipes = recipes[:int(recipes_limit)]
        return AdditionalForRecipeSerializer(recipes, many=True).data

    @staticmethod
    def get_recipes_count(obj):
        """Метод для получения количества рецептов"""

        return obj.recipes.count()


class IngredientInRecipeSerializer(serializers.ModelSerializer):
    """Сериализатор для модели ингредиентов в рецепте."""

    id = serializers.ReadOnlyField(source='ingredient.id')
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit')

    class Meta:

        model = IngredientInRecipe
        fields = ('id', 'name', 'measurement_unit', 'amount')


class RecipeSerializer(serializers.ModelSerializer):
    """Сериализатор для рецептов."""

    tags = TagSerializer(many=True)
    author = UserProfileSerializer()
    ingredients = IngredientInRecipeSerializer(
        source='ingredient_list', many=True)
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:

        model = Recipe
        fields = ('id', 'tags', 'author', 'ingredients',
                  'is_favorited', 'is_in_shopping_cart', 'name',
                  'image', 'text', 'cooking_time'
                  )

    def get_is_favorited(self, obj):
        """Метод проверки на добавление в избранное."""

        request = self.context.get('request')
        if request is None or request.user.is_anonymous:
            return False
        return Favorite.objects.filter(
            user=request.user, recipe=obj
        ).exists()

    def get_is_in_shopping_cart(self, obj):
        """Метод проверки на присутствие в корзине."""

        request = self.context.get('request')
        if request is None or request.user.is_anonymous:
            return False
        return ShoppingCart.objects.filter(
            user=request.user, recipe=obj
        ).exists()

    def validate_recipe_in_favorite(self, recipe, user):
        if Favorite.objects.filter(user=user, recipe=recipe).exists():
            raise serializers.ValidationError(
                f'Рецепт "{recipe.name}" уже в избранном.')

    def validate_recipe_not_in_favorite(self, recipe, user):
        if not Favorite.objects.filter(user=user, recipe=recipe).exists():
            raise serializers.ValidationError(
                f'Рецепта "{recipe.name}" нет в избранном.')

    def validate_recipe_in_cart(self, recipe, user):
        if ShoppingCart.objects.filter(user=user, recipe=recipe).exists():
            raise serializers.ValidationError(
                f'Рецепт "{recipe.name}" уже в корзине.')

    def validate_recipe_not_in_cart(self, recipe, user):
        if not ShoppingCart.objects.filter(user=user, recipe=recipe).exists():
            raise serializers.ValidationError(
                f'Рецепта "{recipe.name}" нет в корзине.')


class CreateIngredientsInRecipeSerializer(serializers.ModelSerializer):
    """Сериализатор для ингредиентов в рецептах"""

    id = serializers.IntegerField()
    amount = serializers.IntegerField()

    @staticmethod
    def validate_amount(value):
        """Метод валидации количества"""

        if value < 1:
            raise serializers.ValidationError(
                'Количество ингредиента должно быть больше 0!'
            )
        return value

    class Meta:

        model = IngredientInRecipe
        fields = ('id', 'amount')


class CreateRecipeSerializer(serializers.ModelSerializer):
    """Сериализатор для создания рецептов"""

    ingredients = CreateIngredientsInRecipeSerializer(many=True)
    tags = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Tag.objects.all()
    )
    image = Base64ImageField(use_url=True)

    class Meta:

        model = Recipe
        fields = ('ingredients', 'tags', 'name',
                  'image', 'text', 'cooking_time')

    def to_representation(self, instance):

        serializer = RecipeSerializer(
            instance,
            context={
                'request': self.context.get('request')
            }
        )
        return serializer.data

    def validate(self, data):
        """Метод валидации ингредиентов"""

        ingredients = self.initial_data.get('ingredients')
        lst_ingredient = []

        for ingredient in ingredients:
            if ingredient['id'] in lst_ingredient:
                raise serializers.ValidationError(
                    'Ингредиенты должны быть уникальными!'
                )
            lst_ingredient.append(ingredient['id'])

        return data

    def create_ingredients(self, ingredients, recipe):
        """Метод создания ингредиента"""

        for element in ingredients:
            id = element['id']
            ingredient = Ingredient.objects.get(pk=id)
            amount = element['amount']
            IngredientInRecipe.objects.create(
                ingredient=ingredient, recipe=recipe, amount=amount
            )

    def create_tags(self, tags, recipe):
        """Метод добавления тега"""

        recipe.tags.set(tags)

    def create(self, validated_data):
        """Метод создания модели"""

        ingredients = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')

        user = self.context.get('request').user
        recipe = Recipe.objects.create(**validated_data, author=user)
        self.create_ingredients(ingredients, recipe)
        self.create_tags(tags, recipe)
        return recipe

    def update(self, instance, validated_data):
        """Метод обновления модели"""

        IngredientInRecipe.objects.filter(recipe=instance).delete()
        TagInRecipe.objects.filter(recipe=instance).delete()

        self.create_ingredients(validated_data.pop('ingredients'), instance)
        self.create_tags(validated_data.pop('tags'), instance)

        return super().update(instance, validated_data)


class AddFavoritesSerializer(serializers.ModelSerializer):
    """Сериализатор для добавления в избранное по модели Recipe."""
    image = Base64ImageField()

    class Meta:
        """Мета-параметры сериализатора"""

        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')
