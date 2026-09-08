# Events Aggregator API

FastAPI-приложение для агрегации событий от Events Provider API с расширенными возможностями для работы с мероприятиями, регистрациями и местами.

## 📋 Содержание

- [Возможности](#-возможности)
- [Технологии](#-технологии)
- [Быстрый старт](#-быстрый-старт)
- [Переменные окружения](#-переменные-окружения)
- [API Endpoints](#-api-endpoints)
- [Структура проекта](#-структура-проекта)
- [Локальная разработка](#-локальная-разработка)
- [Тесты](#-тесты)
- [CI/CD](#-cicd)
- [Деплой](#-деплой)

## ✨ Возможности

- **Фоновая синхронизация** — периодическое обновление событий из Events Provider API (инкрементально через `changed_at`)
- **Ручной запуск синхронизации** — триггер синхронизации по запросу
- **Фильтрация и пагинация** — поиск событий по дате, пагинация по страницам
- **Управление регистрациями** — создание и отмена билетов
- **Кэширование мест** — TTL-кэш (30 сек) для актуального списка доступных мест
- **Health check** — мониторинг доступности сервиса

## 🛠 Технологии

| Компонент | Технология |
|-----------|------------|
| Фреймворк | FastAPI |
| ORM | SQLAlchemy 2.0 (async) |
| База данных | PostgreSQL |
| HTTP-клиент | httpx |
| Миграции | Alembic |
| Сборка | uv |
| Линтинг | Ruff |
| Тесты | pytest + pytest-asyncio |
| Контейнеризация | Docker |

## 🚀 Быстрый старт

```bash
# 1. Клонируйте репозиторий
git clone https://github.com/iadzhak/itk-events-agregator
cd itk-events-agregator

# 2. Создайте .env файл
cp .env.example .env

# 3. Заполните переменные окружения
#    (см. раздел ниже)

# 4. Установите зависимости и примените миграции
uv sync --dev && uv run alembic upgrade head

# 5. Запустите сервер
uv run uvicorn app.main:app --reload

# 5. Откройте документацию
#    http://127.0.0.1:8000/docs
```

## 📝 Переменные окружения

Проект использует `.env` файл. Скопируйте `.env.example` и заполните значения:

| Переменная | Описание | По умолчанию |
|------------|----------|--------------|
| `APP_TITLE` | Заголовок приложения | `Events Aggregator` |
| `APP_DESCRIPTION` | Описание приложения | `Special aggregator for Events Provider API` |
| `ORIGINS` | Список разрешённых CORS-источников (через запятую) | `*` |
| `UPDATE_INTERVAL_H` | Интервал фоновой синхронизации в часах | `24` |
| `PROVIDER_BASE_URL` | Базовый URL Events Provider API | `` |
| `PROVIDER_API_KEY` | API-ключ для Events Provider API | `` |
| `POSTGRES_HOST` | Хост PostgreSQL | `localhost` |
| `POSTGRES_USERNAME` | Имя пользователя PostgreSQL | `postgres` |
| `POSTGRES_PASSWORD` | Пароль PostgreSQL | `postgres` |
| `POSTGRES_DATABASE_NAME` | Имя базы данных PostgreSQL | `postgres` |
| `POSTGRES_PORT` | Порт PostgreSQL | `5432` |

## 🔌 API Endpoints

### Health Check

```
GET /api/health
```

Проверка доступности сервиса.

### События

```
GET /api/events?date_from=YYYY-MM-DD&page=1&page_size=20
```

Получение списка событий с фильтрацией по дате и пагинацией.

```
GET /api/events/{event_id}
```

Детали конкретного события.

```
GET /api/events/{event_id}/seats
```

Список доступных мест на мероприятии (кэш 30 сек).

### Регистрации

```
POST /api/tickets
```

Регистрация на событие.

```
DELETE /api/tickets/{ticket_id}
```

Отмена регистрации.

### Синхронизация

```
POST /api/sync/trigger
```

Ручной запуск синхронизации событий с Events Provider API.

> **Swagger/OpenAPI документация:** `http://127.0.0.1:8000/docs`

## 📁 Структура проекта

```
src/app/
├── api/                    # API endpoints
│   ├── endpoints/          # Маршрутизация
│   │   ├── health.py       # Health check
│   │   ├── events.py       # Информация о мероприятиях
│   │   ├── sync.py         # Синхронизация
│   │   └── tickets.py      # Регистрации
│   └── routers.py          # Группировка роутеров
├── clients/                # HTTP-клиенты
│   ├── base.py             # Базовый интерфейс
│   └── events_provider.py  # Events Provider API client
├── core/                   # Ядро приложения
│   ├── conf.py             # Конфигурация
│   ├── db.py               # Подключение к БД
│   ├── exceptions.py       # Обработка ошибок
│   └── logging.py          # Логирование
├── flows/                  # Use cases (бизнес-логика)
│   ├── create_ticket.py    # Регистрация на событие
│   └── cancel_ticket.py    # Отмена регистрации
├── models/                 # SQLAlchemy модели
│   ├── event.py            # Модель события
│   ├── place.py            # Модель площадки
│   ├── sync.py             # Метаданные синхронизации
│   └── ticket.py           # Модель билета
├── repository/             # Repository pattern
│   ├── base.py             # Базовый репозиторий
│   ├── event.py            # События
│   ├── place.py            # Площадки
│   ├── sync.py             # Синхронизация
│   └── ticket.py           # Билеты
├── schemas/                # Pydantic схемы
│   ├── event.py            # События
│   ├── pagination.py       # Пагинация
│   ├── place.py            # Площадки
│   └── ticket.py           # Билеты
├── services/               # Сервисы
│   ├── event.py            # Логика работы с событиями
│   └── sync.py             # Логика синхронизации
├── types/                  # Типы и перечисления
├── utils/                  # Утилиты
│   └── paginator.py        # EventsPaginator
├── dependencies.py         # Dependency injection
├── lifespan.py             # Управление жизненным циклом
├── background_tasks.py     # Фоновые задачи
└── main.py                 # Точка входа
```

## 💻 Локальная разработка

### Вручную

```bash
# Установка зависимостей
uv sync --dev

# Применение миграций
uv run alembic upgrade head

# Запуск сервера с hot-reload
uv run uvicorn app.main:app --reload

# Запуск линтера
ruff check --fix

# Применение миграций
uv run alembic upgrade head
```

## 🧪 Тесты

Проект использует [pytest](https://docs.pytest.org/) с [pytest-asyncio](https://pytest-asyncio.readthedocs.io/) для асинхронных тестов.

```bash
# Запуск всех тестов
pytest

# Запуск с подробным выводом
pytest -vv

# Запуск только unit-тестов
pytest -m unit

# Запуск только интеграционных тестов
pytest -m integ

# Сброс кэша pytest
pytest --cache-clear
```

### Маркеры тестов

| Маркер | Описание |
|--------|----------|
| `unit` | Юнит-тесты отдельных функций и методов |
| `integ` | Интеграционные тесты — используют testcontainers для запуска PostgreSQL в Docker-контейнере |

> **Примечание:** Маркеры в процессе расширения. Полный список: `pytest --markers`

### Тестирование с PostgreSQL

Интеграционные тесты используют [testcontainers](https://testcontainers-python.readthedocs.io/) для запуска PostgreSQL в Docker-контейнере. Убедитесь, что Docker запущен.

## 🔄 Линтинг

Проект использует [Ruff](https://docs.astral.sh/ruff/) для линтинга и форматирования.

```bash
# Проверка кода
ruff check

# Автоматическое исправление
ruff check --fix

# Форматирование
ruff format
```

## 🚦 CI/CD

GitHub Actions автоматически запускает линтинг перед деплоем:

```yaml
# .github/workflows/deploy.yml
jobs:
  lint:    # Ruff check
  test:    # Pytest unit tests
  build:   # Docker build (multi-platform)
  deploy:  # Deploy request
```

## 🐳 Деплой

### Docker

```bash
# Сборка образа
docker build -t events-aggregator:latest .

# Запуск
docker run -p 8000:8000 --env-file .env events-aggregator:latest
```

### Docker Compose

```bash
docker compose up -d
```

### Production

Для продакшена используйте `run.sh`, который автоматически применяет миграции и запускает uvicorn:

```bash
CMD ["bash", "./run.sh"]
```

## 📄 Лицензия

[Укажите лицензию]
