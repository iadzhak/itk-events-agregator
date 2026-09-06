# Events Aggregator API

FastAPI-приложение для агрегации событий от Events Provider API.

## Переменные окружения

Проект использует `.env` файл. Скопируйте `.env.example` и заполните значения:

```bash
cp .env.example .env
```

| Переменная          | Описание                                           | По умолчанию                                  |
|---------------------|----------------------------------------------------|-----------------------------------------------|
| `APP_TITLE`         | Заголовок приложения                               | `Events Aggregator`                           |
| `APP_DESCRIPTION`   | Описание приложения                                | `Special aggregator for Events Provider API`  |
| `ORIGINS`           | Список разрешённых CORS-источников (через запятую) | `*`                                           |
| `UPDATE_INTERVAL_H` | Интервал обновления данных в часах                 | `24`                                          |
| `PROVIDER_BASE_URL` | Базовый URL Events Provider API                    | `http://events-provider.dev-2.python-labs.ru` |
| `PROVIDER_API_KEY`  | API-ключ для Events Provider API                   | ``                                            |
| `DB_HOST`           | Хост PostgreSQL                                    | `localhost`                                   |
| `POSTGRES_USER`     | Имя пользователя PostgreSQL                        | `postgres`                                    |
| `POSTGRES_PASSWORD` | Пароль PostgreSQL                                  | `postgres`                                    |
| `POSTGRES_DB`       | Имя базы данных PostgreSQL                         | `postgres`                                    |
| `POSTGRES_PORT`     | Порт PostgreSQL                                    | `5432`                                        |

## Линтинг

Проект использует [Ruff](https://docs.astral.sh/ruff/) для линтинга и форматирования.

```bash
# Проверка кода
ruff check

# Автоматическое исправление простых ошибок
ruff check --fix
```

## Тесты

Проект использует [pytest](https://docs.pytest.org/) с [pytest-asyncio](https://pytest-asyncio.readthedocs.io/) для
асинхронных тестов.

```bash
# Запуск всех тестов
pytest

# Запуск только unit-тестов
pytest -m unit
```

### Маркеры тестов

| Маркер | Описание                                  |
|--------|-------------------------------------------|
| `unit` | Юнит-тесты, проверяющие отдельные функции |

Полный список маркеров можно получить через `pytest --markers`.

> **Примечание:** Маркеры в процессе расширения. В данный момент доступен только `unit`.

## Локальная разработка

### Через Make

```bash
make dev
```

### Вручную

```bash
uv run uvicorn app.main:app --reload
```

Сервер запустится на `http://127.0.0.1:8000` с hot-reload.

Документация Swagger доступна по адресу `http://127.0.0.1:8000/docs`.
