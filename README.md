## Описание проекта

«Фудграм» — сайт, на котором пользователи будут публиковать свои рецепты, добавлять чужие рецепты в избранное и подписываться на публикации других авторов. Зарегистрированным пользователям также будет доступен сервис «Список покупок». Он позволит создавать список продуктов, которые нужно купить для приготовления выбранных блюд.
## Как установить

### Установка локально
1. **Клонирование репозитория**  
   Клонируйте репозиторий и перейдите в директорию проекта:
   ```bash
   git clone https://github.com/ekaterina3333/foodgram.git
   ```

2. **Переменные окружения**  
   В корневой папке создайте файл `.env` с необходимыми переменными окружения (пример структуры см. в `.env.example`).

3. **Создание виртуального окружения**  
   Создайте и активируйте виртуальное окружение:
   ```bash
   python -m venv venv
   source venv/bin/activate  # Для Windows: venv\Scripts\activate
   ```

4. **Установка зависимостей**  
   Установите зависимости из файла `requirements.txt`:
   ```bash
   python -m pip install --upgrade pip
   pip install -r requirements.txt
   ```

5. **Применение миграций**  
   Настройте базу данных:
   ```bash
   python manage.py migrate
   ```

6. Соберите статику:
    ```bash
    sudo docker compose -f docker-compose.yml exec backend python manage.py collectstatic
    sudo docker compose -f docker-compose.yml exec backend cp -r /app/collected_static/. /backend_static/static/
    ```

7. Импортируйте ингредиенты и теги:
    ```bash
    sudo docker compose -f docker-compose.yml exec backend python manage.py import_ingredients
    sudo docker compose -f docker-compose.yml exec backend python manage.py import_tags
    ```

8. Создайте суперпользователя:
    ```bash
    sudo docker compose -f docker-compose.yml exec backend python manage.py createsuperuser
    ```
    
9. **Локально запуск сервера**  
   Запустите локальный сервер:
   ```bash
   python manage.py runserver
   ```
---

## Технологии

- Python 3.9
- Django 3.2.16
- Django REST framework 3.14.0
- JavaScript
## Автор

Тяжова Екатерина https://t.me/pretenzii_syda
Админка ekaterina 105cinos

