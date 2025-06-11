from django.contrib.auth.models import AbstractUser
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.db import models

from .constants import MAX_LENGTH_EMAIL, MAX_LENGTH


class User(AbstractUser):
    """Модель для пользователей созданная для приложения foodgram"""

    email = models.CharField(
        max_length=MAX_LENGTH_EMAIL,
        verbose_name='Адрес электронной почты',
        unique=True
    )
    username = models.CharField(
        max_length=MAX_LENGTH,
        verbose_name='Уникальный юзернейм',
        unique=True,
        db_index=True,
        validators=[UnicodeUsernameValidator],
    )
    first_name = models.CharField(
        max_length=MAX_LENGTH,
        verbose_name='Имя'
    )
    last_name = models.CharField(
        max_length=MAX_LENGTH,
        verbose_name='Фамилия'
    )
    avatar = models.ImageField(
        upload_to='users/avatars/',
        blank=True,
        null=True,
        verbose_name='Аватар',
    )

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    class Meta:

        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        ordering = ('id',)

    def __str__(self):
        return self.username
