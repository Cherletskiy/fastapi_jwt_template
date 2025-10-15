# FastAPI JWT

REST API на FastAPI для реализации аутентификации на основе JWT с использованием `access_token` и `refresh_token` (хранится в `HttpOnly` куках). Поддерживает регистрацию, вход, обновление токенов, получение профиля и выход пользователя. Используется PostgreSQL для хранения данных и pgAdmin для администрирования БД.

## Возможности
- Регистрация и вход пользователей с JWT-аутентификацией.
- `access_token` (действует 30 минут) и `refresh_token` (действует 7 дней) в `HttpOnly` куках.
- Эндпоинты: `/register`, `/login`, `/refresh`, `/refresh-body`, `/me`, `/logout`.
- Интеграционные тесты с покрытием кода 81%.
- Логирование запросов и ошибок.
- Хеширование паролей с использованием bcrypt.
- Упаковка в Docker с PostgreSQL и pgAdmin.
- Swagger UI для документации API.

## Требования
- Python 3.11+
- Docker и Docker Compose
- Зависимости: указаны в `requirements.txt`

## Структура проекта
```
fastapi_jwt_template/
├── app/
│   ├── api/
│   │   └── v1/
│   │       ├── auth.py          # Эндпоинты аутентификации
│   │       └── schemas.py       # Pydantic-схемы
│   ├── core/
│   │   ├── config.py            # Настройки приложения
│   │   ├── database.py          # Настройка БД
│   │   ├── dependencies.py      # Зависимости FastAPI
│   │   ├── logging_config.py    # Настройка логирования
│   │   ├── migrations.py        # Миграции БД
│   │   └── security.py          # Аутентификация
│   ├── models/
│   │   └── user.py              # Модель пользователя
│   ├── repositories/
│   │   └── user_repository.py   # Репозиторий для работы с пользователями
│   ├── services/
│   │   └── user_service.py      # Сервис для бизнес-логики
│   ├── tests/
│   │   ├── conftest.py          # Конфигурация pytest
│   │   └── test_auth.py         # Тесты
│   └── main.py                  # Точка входа приложения
├── alembic/
│   ├── versions/                # Файлы миграций
│   └── env.py                   # Настройка Alembic
├── .coveragerc                  # Настройка pytest-cov
├── .env                         # Переменные окружения
├── alembic.ini                  # Конфигурация Alembic
├── Dockerfile                   # Docker-образ приложения
├── docker-compose.yml           # Конфигурация Docker Compose
├── requirements.txt             # Зависимости
└── README.md                    # Документация
```

## Модель данных
Модель `User` (таблица `users` в PostgreSQL):
- **id**: `int`, первичный ключ, автоинкремент.
- **username**: `str`, уникальное имя пользователя.
- **email**: `str`, уникальный email.
- **hashed_password**: `str`, хеш пароля (bcrypt).
- **created_at**: `datetime`, дата создания записи.

## Установка и запуск
1. **Клонируйте репозиторий**:
   ```bash
   git clone <repository_url>
   cd fastapi_jwt_template
   ```

2. **Настройте переменные окружения**:
   - Скопируйте `.env.example` в `.env` и обновите:
     ```env
     DB_HOST=db
     DB_PORT=5432
     DB_USER=your_user
     DB_NAME=your_db
     DB_PASSWORD=your_password
     PGADMIN_DEFAULT_EMAIL=admin@admin.com
     PGADMIN_DEFAULT_PASSWORD=admin
     SECRET_KEY=your_secret_key
     ALGORITHM=HS256
     ACCESS_TOKEN_EXPIRE_MINUTES=30
     REFRESH_TOKEN_EXPIRE_DAYS=7
     ```

3. **Установите зависимости** (опционально, для локального запуска):
   ```bash
   pip install -r requirements.txt
   ```

4. **Запустите с помощью Docker**:
   ```bash
   docker-compose up -d
   ```
   - Приложение: `http://localhost:8000`
   - Swagger UI: `http://localhost:8000/docs`
   - pgAdmin: `http://localhost:5050` (логин: `admin@admin.com`, пароль: `admin`)

5. **Запустите тесты**:
   ```bash
   docker-compose exec app pytest app/tests -v --cov=app --cov-report=term
   ```

## Настройка pgAdmin
- Доступ: `http://localhost:5050`
- Логин: `PGADMIN_DEFAULT_EMAIL` (по умолчанию `admin@admin.com`)
- Пароль: `PGADMIN_DEFAULT_PASSWORD` (по умолчанию `admin`)
- Добавьте сервер PostgreSQL:
  - Host: `db`
  - Port: `5432`
  - Username: `postgres` (из `.env`)
  - Password: `postgres` (из `.env`)
  - Database: `postgres` (из `.env`)

## Описание эндпоинтов
| Эндпоинт | Метод | Описание | Параметры | Ответ |
|----------|-------|----------|-----------|-------|
| `/api/v1/auth/register` | POST | Регистрация нового пользователя | JSON: `username`, `email`, `password` | 200: Данные пользователя (`id`, `username`, `email`, `created_at`) <br> 400: `Email already registered` |
| `/api/v1/auth/login` | POST | Аутентификация пользователя | JSON: `email`, `password` | 200: `{access_token, token_type}` + `refresh_token` в `HttpOnly` куки <br> 401: `Invalid credentials` |
| `/api/v1/auth/refresh` | POST | Обновление `access_token` через куки | `refresh_token` в куки | 200: `{access_token, token_type}` + новый `refresh_token` в куки <br> 401: `No refresh token provided` или `Invalid token` |
| `/api/v1/auth/refresh-body` | POST | Обновление `access_token` через тело запроса | JSON: `token` (`refresh_token`) | 200: `{access_token, token_type}` + новый `refresh_token` в куки <br> 401: `Invalid token` |
| `/api/v1/auth/me` | GET | Получение профиля текущего пользователя | Header: `Authorization: Bearer <access_token>` | 200: Данные пользователя (`id`, `username`, `email`, `created_at`) <br> 401: `Not authenticated` |
| `/api/v1/auth/logout` | POST | Выход пользователя | Header: `Authorization: Bearer <access_token>` | 200: `{"message": "Logged out"}`, удаляет `refresh_token` из куки <br> 401: `Not authenticated` |

## Ручное тестирование эндпоинтов
Используйте Postman, cURL или Swagger UI (`http://localhost:8000/docs`).

### 1. Регистрация (`/register`)
- **Запрос**:
  ```bash
  curl -X POST http://localhost:8000/api/v1/auth/register \
    -H "Content-Type: application/json" \
    -d '{"username":"testuser","email":"test@example.com","password":"Secure123"}'
  ```
- **Ответ** (200):
  ```json
  {"id":1,"username":"testuser","email":"test@example.com","created_at":"2025-10-15T12:00:00"}
  ```
- **Ошибка** (400):
  ```json
  {"detail":"Email already registered"}
  ```

### 2. Вход (`/login`)
- **Запрос**:
  ```bash
  curl -X POST http://localhost:8000/api/v1/auth/login \
    -H "Content-Type: application/json" \
    -d '{"email":"test@example.com","password":"Secure123"}' \
    -c cookies.txt
  ```
- **Ответ** (200):
  ```json
  {"access_token":"eyJ...","token_type":"bearer"}
  ```
  - `refresh_token` в `cookies.txt` как `HttpOnly` куки.
- **Ошибка** (401):
  ```json
  {"detail":"Invalid credentials"}
  ```

### 3. Обновление токена (`/refresh`)
- **Запрос**:
  ```bash
  curl -X POST http://localhost:8000/api/v1/auth/refresh \
    -b cookies.txt \
    -c cookies.txt
  ```
- **Ответ** (200):
  ```json
  {"access_token":"eyJ...","token_type":"bearer"}
  ```
  - Новый `refresh_token` в куки.
- **Ошибка** (401):
  ```json
  {"detail":"No refresh token provided"}
  ```

### 4. Обновление токена через тело (`/refresh-body`)
- **Запрос**:
  ```bash
  curl -X POST http://localhost:8000/api/v1/auth/refresh-body \
    -H "Content-Type: application/json" \
    -d '{"token":"eyJ..."}' \
    -c cookies.txt
  ```
- **Ответ** (200):
  ```json
  {"access_token":"eyJ...","token_type":"bearer"}
  ```
  - Новый `refresh_token` в куки.
- **Ошибка** (401):
  ```json
  {"detail":"Invalid token"}
  ```

### 5. Получение профиля (`/me`)
- **Запрос**:
  ```bash
  curl -X GET http://localhost:8000/api/v1/auth/me \
    -H "Authorization: Bearer <access_token>"
  ```
- **Ответ** (200):
  ```json
  {"id":1,"username":"testuser","email":"test@example.com","created_at":"2025-10-15T12:00:00"}
  ```
- **Ошибка** (401):
  ```json
  {"detail":"Not authenticated"}
  ```

### 6. Выход (`/logout`)
- **Запрос**:
  ```bash
  curl -X POST http://localhost:8000/api/v1/auth/logout \
    -H "Authorization: Bearer <access_token>" \
    -c cookies.txt
  ```
- **Ответ** (200):
  ```json
  {"message":"Logged out"}
  ```
  - Удаляет `refresh_token` из куки.
- **Ошибка** (401):
  ```json
  {"detail":"Not authenticated"}
  ```

### Тестирование в Swagger
1. Откройте `http://localhost:8000/docs`.
2. Нажмите **Authorize** (иконка замка), введите `access_token` из `/login` для `/me` и `/logout`.
3. Для `/refresh-body` используйте `refresh_token` из DevTools (Application → Cookies).

## Покрытие тестами
Интеграционные тесты покрывают 81% кода. Отчёт:

| Файл                            | Строк | Пропущено | Покрытие |
|--------------------------------|-------|-----------|----------|
| app/__init__.py                | 0     | 0         | 100%     |
| app/api/__init__.py            | 0     | 0         | 100%     |
| app/api/v1/__init__.py         | 0     | 0         | 100%     |
| app/api/v1/auth.py             | 51    | 0         | 100%     |
| app/api/v1/schemas.py          | 26    | 1         | 96%      |
| app/core/__init__.py           | 0     | 0         | 100%     |
| app/core/config.py             | 15    | 0         | 100%     |
| app/core/database.py           | 18    | 9         | 50%      |
| app/core/dependencies.py       | 29    | 0         | 100%     |
| app/core/logging_config.py     | 14    | 0         | 100%     |
| app/core/migrations.py         | 13    | 8         | 38%      |
| app/core/security.py           | 56    | 10        | 82%      |
| app/main.py                    | 20    | 9         | 55%      |
| app/models/__init__.py         | 0     | 0         | 100%     |
| app/models/user.py             | 13    | 0         | 100%     |
| app/repositories/__init__.py   | 0     | 0         | 100%     |
| app/repositories/user_repository.py | 21 | 9      | 57%      |
| app/services/__init__.py       | 0     | 0         | 100%     |
| app/services/user_service.py   | 34    | 12        | 65%      |
| **Итого**                      | **310** | **58**  | **81%**  |


## Планы доработки
- Добавить rate-limiting для `/login` (защита от brute-force).
- Добавить blacklist токенов для `/logout`.
- Доработать обработку ошибок.
- Доработать логирование.
- Добавить docstring.
- Увеличить покрытие тестов, разбить тесты на несколько файлов. 
- CI/CD.