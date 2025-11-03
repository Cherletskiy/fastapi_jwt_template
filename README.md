# FastAPI JWT RBAC Template

## Ветка rbac-auth для ТЗ Effective Mobile

REST API на FastAPI для реализации аутентификации на основе JWT с системой ролей и разрешений (RBAC). Поддерживает регистрацию, вход, обновление токенов, управление профилем, мягкое удаление пользователей и контроль доступа на основе ролей.


#### Приложение ещё не обернуто в docker, реализую в ближайшее время. 

## Возможности

- **Аутентификация JWT**: `access_token` (действует 30 минут) и `refresh_token` (действует 7 дней) в `HttpOnly` куках
- **Система RBAC**: Роли (user, moderator, admin) и разрешения с гибкой настройкой прав доступа
- **Управление пользователями**: 
  - Расширенная модель пользователя (имя, фамилия, отчество)
  - Мягкое удаление (деактивация) пользователей
  - Обновление профиля
- **Безопасность**:
  - Хеширование паролей с использованием bcrypt
  - Blacklist отозванных токенов через Redis
  - Валидация данных через Pydantic
- **Администрирование**: Панели модератора и администратора с разграничением прав доступа (пока без функционала)
- **Тестирование**: Интеграционные тесты и юнит-тесты с покрытием кода 87%
- **Логирование**: Детальное логирование запросов и ошибок
- **Документация**: Swagger UI для интерактивной документации API

## Требования

- Python 3.12+
- PostgreSQL 16-17
- Redis 7+
- Зависимости: указаны в `requirements.txt`

## Структура проекта

```
fastapi_jwt_template/
├── app/
│   ├── api/
│   │   └── v1/
│   │       ├── admin.py          # Эндпоинты админ-панели
│   │       ├── auth.py           # Эндпоинты аутентификации
│   │       ├── schemas.py        # Pydantic-схемы
│   │       └── users.py          # Эндпоинты пользователей
│   ├── core/
│   │   ├── config.py             # Настройки приложения
│   │   ├── database.py           # Настройка БД
│   │   ├── dependencies.py       # Зависимости FastAPI
│   │   ├── exceptions.py         # Обработка исключений
│   │   ├── logging_config.py     # Настройка логирования
│   │   ├── migrations.py         # Миграции БД
│   │   ├── redis.py              # Redis клиент
│   │   └── security.py           # Аутентификация и безопасность
│   ├── models/
│   │   ├── base.py               # Базовая модель
│   │   ├── rbac.py               # Модели RBAC (роли, разрешения)
│   │   └── user.py               # Модель пользователя
│   ├── repositories/
│   │   ├── rbac_repository.py    # Репозиторий для работы с RBAC
│   │   └── user_repository.py    # Репозиторий для работы с пользователями
│   ├── services/
│   │   ├── authorization_service.py  # Сервис авторизации RBAC
│   │   └── user_service.py       # Сервис для бизнес-логики пользователей
│   ├── tests/
│   │   ├── conftest.py           # Конфигурация pytest
│   │   ├── test_auth_endpoints.py
│   │   ├── test_authorization_service.py
│   │   ├── test_integration.py
│   │   ├── test_security_utils.py
│   │   └── test_user_service.py
│   └── main.py                   # Точка входа приложения
├── alembic/
│   ├── versions/                 # Файлы миграций
│   └── env.py                    # Настройка Alembic
├── .coveragerc                   # Настройка pytest-cov
├── .env.example                  # Пример переменных окружения
├── alembic.ini                   # Конфигурация Alembic
├── docker-compose.yml            # Конфигурация Docker Compose
├── Dockerfile                    # Docker-образ приложения
├── requirements.txt              # Зависимости
└── README.md                     # Документация
```

## Модель данных

### Пользователь (`users` таблица)
- **id**: `int`, первичный ключ, автоинкремент
- **username**: `str`, nickname (пока заглушка, можно удалить или доработать)
- **email**: `str`, уникальный email
- **hashed_password**: `str`, хеш пароля (bcrypt)
- **first_name**: `str`, имя
- **last_name**: `str`, фамилия  
- **middle_name**: `str`, отчество
- **is_active**: `bool`, активен ли пользователь
- **created_at**: `datetime`, дата создания записи

### RBAC Модели
- **roles**: Роли пользователей (user, moderator, admin)
- **permissions**: Разрешения (profile:read, profile:write, users:read, users:write, admin:access)
- **user_roles**: Связь пользователей с ролями
- **role_permissions**: Связь ролей с разрешениями

## Установка и запуск

### 1. Клонируйте репозиторий
```bash
git clone <repository_url>
cd fastapi_jwt_template
```

### 2. Настройте переменные окружения
Скопируйте `.env.example` в `.env` и обновите:
```env
DB_NAME=postgres
DB_USER=postgres
DB_PWD=postgres
DB_HOST=db
DB_PORT=5432

TEST_DB_NAME=test_jwt_db
TEST_DB_USER=postgres
TEST_DB_PWD=postgres
TEST_DB_HOST=test_db
TEST_DB_PORT=5432

PGADMIN_DEFAULT_EMAIL=admin@admin.com
PGADMIN_DEFAULT_PASSWORD=admin

REDIS_HOST=redis
REDIS_PORT=6379
REDIS_PASSWORD=
REDIS_DB=0

SECRET_KEY=your_secret_key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

LOCAL_APP=False - параметр для запуска app локально
```

### 2. Запустите Docker Compose
```bash
docker-compose up -d 
```

### 3. Доступ к сервисам
- **Приложение**: `http://localhost:8000`
- **Swagger UI**: `http://localhost:8000/docs`
- **pgAdmin**: `http://localhost:8080` (логин: `admin@admin.com`, пароль: `admin`)

## RBAC Система

### Предустановленные роли и разрешения

При миграции автоматически создаются:

#### Роли:
- **user**: Обычный пользователь
- **moderator**: Модератор  
- **admin**: Администратор

#### Разрешения:
- `profile:read` - Чтение профиля
- `profile:write` - Редактирование профиля
- `users:read` - Просмотр пользователей
- `users:write` - Редактирование пользователей
- `admin:access` - Доступ к админ-панели

#### Назначения прав:
- **user**: `profile:read`, `profile:write`
- **moderator**: `profile:read`, `profile:write`, `users:read`
- **admin**: Все разрешения

#### Тестовые пользователи:
- **user@example.com** / `password123` - роль `user`
- **admin@example.com** / `password123` - роль `admin`

## Эндпоинты API

> **Документация** также доступна в `Swagger UI`: http://localhost:8000/docs  
> **Примечание:** аутентификация через форму в Swagger не работает.  
> Рекомендуется использовать `Postman` или `curl` для тестирования.

### Аутентификация (`/api/v1/auth`)

| Эндпоинт | Метод | Описание | Доступ | Ответ |
|----------|-------|----------|--------|-------|
| `/register` | **POST** | Регистрация нового пользователя | Публичный | **200** – данные пользователя (`id`, `username`, `email`, `first_name`, `last_name`, `middle_name`, `created_at`)<br>**400** – `Email already registered` или ошибки валидации |
| `/login` | **POST** | Аутентификация пользователя | Публичный | **200** – `{access_token, token_type}` + `refresh_token` в `HttpOnly`-куке<br>**401** – `Invalid credentials` |
| `/refresh` | **POST** | Обновление `access_token` через куку | Публичный (нужен `refresh_token`) | **200** – `{access_token, token_type}` + новый `refresh_token` в куке<br>**401** – `No refresh token provided` / `Invalid token` |
| `/logout` | **POST** | Выход пользователя с отзывом токенов | Аутентифицированные (`access_token`) | **200** – `{"message":"Logged out successfully","tokens_revoked":{...}}`<br>**401** – `Not authenticated` |

---

### Пользователи (`/api/v1/users`)

| Эндпоинт | Метод | Описание | Доступ | Ответ |
|----------|-------|----------|--------|-------|
| `/me` | **GET** | Получение профиля текущего пользователя | Аутентифицированные | **200** – полные данные пользователя (включая `is_active`)<br>**401** – `Not authenticated` / `User account is inactive` |
| `/me` | **PATCH** | Обновление любых полей профиля (можно частично) | Аутентифицированные | **200** – обновлённые данные пользователя<br>**400** – ошибки валидации (например, email уже занят) |
| `/deactivate` | **DELETE** | Мягкое удаление (деактивация) аккаунта | Аутентифицированные | **200** – `{"message":"User <email> deactivated"}`<br>**401** – `Not authenticated` |

---

### Администрирование (`/api/v1/admin`) *(заглушки для проверки RBAC)*

| Эндпоинт | Метод | Описание | Доступ | Ответ                                                                                                                                          |
|----------|-------|----------|--------|------------------------------------------------------------------------------------------------------------------------------------------------|
| `/moderation` | **GET** | Панель модерации (доступна модераторам и админам) | `moderator` **или** `admin` | **200** – Приветсствие<br>**403** – `Insufficient permissions` |
| `/admin_panel` | **GET** | Админ-панель (только админы) | `admin` | **200** – Приветсствие<br>**403** – `Insufficient permissions`                                                                                 |


> **Примечание** – все ответы возвращаются в JSON-формате. Для запросов, требующих аутентификации, в заголовке `Authorization: Bearer <access_token>`.  
> `refresh_token` хранится в `HttpOnly`-куке и автоматически подставляется браузером.  
> При `logout` токены добавляются в blacklist (Redis) и кука `refresh_token` удаляется.

## Тестирование

### Запуск тестов
```bash
docker-compose exec app pytest app/tests -v --cov=app --cov-report=term
```

### Покрытие тестами 87% кода.
```markdown
Name                                    Stmts   Miss  Cover
-----------------------------------------------------------
app/__init__.py                             0      0   100%
app/api/__init__.py                         0      0   100%
app/api/v1/__init__.py                      0      0   100%
app/api/v1/admin.py                        14      0   100%
app/api/v1/auth.py                         50      2    96%
app/api/v1/schemas.py                      50      1    98%
app/api/v1/users.py                        22      3    86%
app/core/__init__.py                        0      0   100%
app/core/config.py                         48     10    79%
app/core/database.py                       18      4    78%
app/core/dependencies.py                   48      6    88%
app/core/exceptions.py                     27      3    89%
app/core/logging_config.py                 14      0   100%
app/core/migrations.py                     27      6    78%
app/core/redis.py                          32      7    78%
app/core/security.py                      113     28    75%
app/main.py                                40      5    88%
app/models/__init__.py                      0      0   100%
app/models/base.py                          4      0   100%
app/models/rbac.py                         28      0   100%
app/models/user.py                         17      0   100%
app/repositories/__init__.py                0      0   100%
app/repositories/rbac_repository.py        39     10    74%
app/repositories/user_repository.py        27      7    74%
app/services/__init__.py                    0      0   100%
app/services/authorization_service.py      34      0   100%
app/services/user_service.py               57      3    95%
-----------------------------------------------------------
TOTAL                                     709     95    87%
```


Основные тестовые сценарии:
- Аутентификация и регистрация
- RBAC авторизация
- Управление профилем пользователя
- Интеграционные тесты полного цикла
- Тесты безопасности

## Ручное тестирование

### 1. Регистрация пользователя
```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "email": "test@example.com", 
    "password": "Secure123",
    "confirm_password": "Secure123",
    "first_name": "Иван",
    "last_name": "Петров",
    "middle_name": "Сергеевич"
  }'
```

### 2. Вход в систему
```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "password": "Secure123"}' \
  -c cookies.txt
```

### 3. Получение профиля
```bash
curl -X GET http://localhost:8000/api/v1/users/me \
  -H "Authorization: Bearer <access_token>"
```

### 4. Обновление профиля
```bash
curl -X PATCH http://localhost:8000/api/v1/users/me \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{"first_name": "НовоеИмя"}'
```

### 5. Доступ к админ-панели (только для admin)
```bash
curl -X GET http://localhost:8000/api/v1/admin/admin_panel \
  -H "Authorization: Bearer <access_token>"
```

## Настройка pgAdmin

1. Откройте `http://localhost:8080`
2. Войдите с credentials из `.env`
3. Добавьте сервер PostgreSQL:
   - **Name**: Любое имя
   - **Host**: `db` 
   - **Port**: `5432`
   - **Username**: `postgres` (из `.env`)
   - **Password**: `postgres` (из `.env`)

## Безопасность

- Пароли хешируются с использованием bcrypt
- JWT токены подписываются секретным ключом
- Refresh токены хранятся в HttpOnly куках
- Реализован blacklist отозванных токенов через Redis
- Валидация входных данных через Pydantic

## Примечание

- Миграция с тестовыми данными нужна для демонстрации, в дальнейшем нужно удалить тестовых пользователей