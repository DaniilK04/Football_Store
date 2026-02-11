# Football Store — интернет-магазин футбольной экипировки

Полноценный fullstack-проект интернет-магазина с backend на Django REST Framework и frontend на чистом HTML/CSS/JS (без фреймворков).

Цель проекта — продемонстрировать навыки работы с REST API, авторизацией, корзиной, заказами и медиафайлами.

## Основные технологии

**Backend**
- Django 6.0.1
- Django REST Framework
- Djoser + Token Authentication
- PostgreSQL
- psycopg2
- django-cors-headers
- REST API с пагинацией, фильтрацией и поиском

**Frontend**
- HTML + CSS (чистый, без фреймворков)
- JavaScript (vanilla + fetch)
- Адаптивная вёрстка
- Локальное хранение токена (localStorage)
- Динамическая загрузка категорий и товаров

**Дополнительно**
- Регистрация и авторизация (Djoser)
- Корзина (добавление/удаление/оформление заказа)
- Загрузка и отображение изображений товаров
- Защита от несанкционированного доступа (токены)

## Основные возможности

- Просмотр каталога товаров с фильтрацией по категориям
- Детальная страница товара
- Добавление товаров в корзину (требуется авторизация)
- Просмотр и оформление заказа из корзины
- Регистрация и вход в личный кабинет
- Адаптивный дизайн (мобильная версия)

## Установка и запуск (локально)

1. Клонируй репозиторий

```bash
git clone https://github.com/DaniilK04/Football_Store.git
cd Football_Store/Backend

Создай и активируй виртуальное окружение

python -m venv .venv
.\.venv\Scripts\activate

Установи зависимости

pip install -r requirements.txt

Создай файл .env в корне проекта с содержимым:

SECRET_KEY='ваш_секретный_ключ'
POSTGRES_DB=shopbd
POSTGRES_USER=shopbd
POSTGRES_PASSWORD='ваш_пароль'
POSTGRES_HOST=localhost
POSTGRES_PORT=5432

Создай базу данных PostgreSQL и примени миграции

python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser

Запусти сервер

python manage.py runserver

Открой фронтенд

В отдельном терминале:
cd Frontend
python -m http.server 8001
Перейди по адресу: http://localhost:8001

API Endpoints (основные)

GET /api/v1/product/ — список товаров
GET /api/v1/product/<slug>/ — детальная страница товара
POST /auth/token/login/ — вход
POST /auth/users/ — регистрация
POST /api/cart/item/add/ — добавить в корзину
GET /api/cart/ — получить корзину
POST /api/v1/order/create-from-cart/ — оформить заказ
