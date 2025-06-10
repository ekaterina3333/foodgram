from django.core.validators import RegexValidator

USERNAME_VALIDATOR = RegexValidator(
    regex=r'^[\w.@+-]+$',
    message='Имя может содержать только буквы, цифры, символы @/./+/-/_'
)

MAX_LENGTH = 150
MAX_LENGTH_EMAIL = 254
