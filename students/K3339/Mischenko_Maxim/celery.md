# Лабораторная работа 3: Упаковка FastAPI приложения в Docker, Работа с источниками данных и Очереди

## Подзадача 3: Вызов парсера из FastAPI через очередь

### Реализация

#### 1. Установка Celery и Redis

Добавлены зависимости в `requirements.txt`:
- `celery==5.3.4` - для обработки фоновых задач
- `redis==5.0.1` - в качестве брокера сообщений и хранилища результатов
- `flower==2.0.1` - для мониторинга задач Celery

#### 2. Настройка Celery

Созданы следующие файлы конфигурации:

**celery_config.py** - основной файл конфигурации Celery:
- Настроен Redis в качестве брокера и бэкенда
- Определены настройки сериализации, тайм-ауты, лимиты задач
- Настроены маршруты задач (очередь `parsing`)

**celery_tasks.py** - файл с определениями задач:
- `parse_url_task` - задача для парсинга одного URL
- `batch_parse_task` - задача для пакетного парсинга нескольких URL
- `health_check_task` - задача для проверки здоровья Celery worker

#### 3. Обновление FastAPI приложения

В файл `main.py` добавлены:

**Новые модели Pydantic:**
- `AsyncParseRequest` - для асинхронного парсинга
- `BatchParseRequest` - для пакетного парсинга
- `TaskResponse` - ответ с информацией о задаче

**Новые эндпоинты:**

1. `POST /parse/async` - Асинхронный парсинг URL
   - Принимает URL в теле запроса
   - Ставит задачу в очередь Celery
   - Возвращает `task_id` для отслеживания статуса

2. `POST /parse/batch` - Пакетный асинхронный парсинг
   - Принимает список URL в теле запроса
   - Ставит задачу в очередь Celery
   - Возвращает `task_id` для отслеживания статуса

3. `GET /tasks/{task_id}/status` - Получение статуса задачи
   - Возвращает текущий статус задачи (PENDING, STARTED, SUCCESS, FAILURE)
   - Если задача завершена, возвращает результат

4. `GET /celery/health` - Проверка здоровья Celery worker
   - Проверяет доступность Celery worker

#### 4. Обновление Docker Compose

В файл `docker-compose.yml` добавлены новые сервисы:

**Redis:**
- Использует образ `redis:7-alpine`
- Порт 6379
- Настроен healthcheck
- Постоянное хранилище данных

**Celery Worker:**
- Запускает Celery worker с 4 процессами
- Зависит от Redis и PostgreSQL
- Использует ту же конфигурацию, что и FastAPI приложение

**Celery Beat**:
- Для выполнения периодических задач по расписанию
- Зависит от Redis и PostgreSQL
- Автоматически запускает задачи по расписанию, определенному в `celery_config.py`

**Flower:**
- Веб-интерфейс для мониторинга Celery
- Доступен по адресу http://localhost:5555
- Показывает статус задач, workers, очереди

**Обновлен сервис fastapi-app:**
- Добавлена переменная окружения `REDIS_URL`
- Добавлена зависимость от Redis

### Конфигурация периодических задач (Celery Beat)

В файле `celery_config.py` настроены периодические задачи, которые автоматически выполняются по расписанию:

#### Настроенные задачи:

1. **health-check-every-2-min** - Проверка здоровья Celery worker
   - Задача: `health_check_task`
   - Расписание: Каждые 2 минуты (120 секунд)
   - Очередь: `default`

2. **daily-batch-parse** - Ежедневный пакетный парсинг важных URL
   - Задача: `batch_parse_task`
   - Расписание: Ежедневно в 3:00 AM
   - URL: https://example.com, https://httpbin.org, https://jsonplaceholder.typicode.com
   - Очередь: `parsing`

3. **test-parse-every-10-min** - Тестовый парсинг для демонстрации
   - Задача: `parse_url_task`
   - Расписание: Каждые 10 минут
   - URL: https://httpbin.org/html
   - Очередь: `parsing`

4. **weekly-health-report** - Еженедельный отчет о здоровье системы
   - Задача: `health_check_task`
   - Расписание: Каждый понедельник в 9:00 AM
   - Очередь: `reports`

5. **hourly-test-task** - Ежечасная тестовая задача
   - Задача: `parse_url_task`
   - Расписание: Каждый час в 0 минут
   - URL: https://httpbin.org/get
   - Очередь: `parsing`

#### Типы расписаний:
- **Интервалы**: Задачи выполняются через фиксированные промежутки времени (например, каждые 2 минуты)
- **Cron-выражения**: Задачи выполняются по сложному расписанию (например, ежедневно в 3:00 AM)

#### Маршрутизация задач:
Задачи направляются в разные очереди для лучшего управления:
- `parsing` - задачи парсинга веб-страниц
- `default` - стандартные задачи (проверка здоровья)
- `reports` - задачи генерации отчетов

### Архитектура решения

```
┌─────────────────┐    HTTP    ┌─────────────────┐
│                 │───────────▶│                 │
│   FastAPI App   │            │   Redis Broker  │
│   (Port 8000)   │◀───────────│   (Port 6379)   │
│                 │   Celery   │                 │
└─────────────────┘   Tasks    └─────────────────┘
         │                           │
         │                           │
         ▼                           ▼
┌─────────────────┐         ┌─────────────────┐
│                 │         │                 │
│   Parser App    │         │  Celery Worker  │
│   (Port 8001)   │         │   (4 processes) │
│                 │         │                 │
└─────────────────┘         └─────────────────┘
         │                           │
         │                           │
         ▼                           ▼
┌─────────────────┐         ┌─────────────────┐
│                 │         │                 │
│   PostgreSQL    │         │    Flower UI    │
│   (Port 5432)   │         │   (Port 5555)   │
│                 │         │                 │
└─────────────────┘         └─────────────────┘
```

### Использование API

#### 1. Асинхронный парсинг одного URL

```bash
curl -X POST "http://localhost:8000/parse/async" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token>" \
  -d '{"url": "https://example.com"}'
```

**Ответ:**
```json
{
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "pending",
  "message": "Задача на парсинг URL поставлена в очередь",
  "url": "https://example.com",
  "check_status_url": "/tasks/550e8400-e29b-41d4-a716-446655440000/status"
}
```

#### 2. Проверка статуса задачи

```bash
curl -X GET "http://localhost:8000/tasks/550e8400-e29b-41d4-a716-446655440000/status" \
  -H "Authorization: Bearer <token>"
```

**Ответ (в процессе выполнения):**
```json
{
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "STARTED",
  "ready": false,
  "successful": false,
  "failed": false
}
```

**Ответ (после завершения):**
```json
{
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "SUCCESS",
  "ready": true,
  "successful": true,
  "failed": false,
  "result": {
    "status": "success",
    "url": "https://example.com",
    "title": "Example Domain",
    "message": "Successfully parsed: Example Domain...",
    "task_id": "550e8400-e29b-41d4-a716-446655440000",
    "task_status": "completed",
    "completed_at": 1744646400.0
  }
}
```

#### 3. Пакетный парсинг

```bash
curl -X POST "http://localhost:8000/parse/batch" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token>" \
  -d '{"urls": ["https://example.com", "https://google.com"]}'
```

### Запуск приложения

```bash
# Запуск всех сервисов
docker-compose up -d

# Просмотр логов
docker-compose logs -f

# Остановка всех сервисов
docker-compose down

# Остановка с удалением volumes
docker-compose down -v
```

### Доступные сервисы после запуска

1. **FastAPI App**: http://localhost:8000
   - Документация API: http://localhost:8000/docs
   - Альтернативная документация: http://localhost:8000/redoc

2. **Parser App**: http://localhost:8001
   - Отдельный сервис парсинга

3. **Flower (Celery Monitoring)**: http://localhost:5555
   - Мониторинг задач, workers, очередей

4. **Redis**: localhost:6379
   - Брокер сообщений для Celery

### Мониторинг и отладка

#### Flower Dashboard
Flower предоставляет веб-интерфейс для мониторинга:
- Список всех задач с их статусами
- Информация о workers
- Графики производительности
- Управление задачами (отмена, повтор)

#### Проверка здоровья Redis
```bash
docker-compose exec redis redis-cli ping
```

#### Проверка здоровья Celery
```bash
curl http://localhost:8000/celery/health
```

#### Просмотр логов Celery worker
```bash
docker-compose logs celery-worker
```

### Особенности реализации

1. **Обработка ошибок**: Задачи Celery корректно обрабатывают ошибки парсинга и возвращают информативные сообщения.

2. **Отслеживание прогресса**: Для пакетных задач реализовано отслеживание прогресса через `update_state`.

3. **Интеграция с существующим кодом**: Задачи используют существующую функцию `parse_and_save` из `parser_app.py`.

4. **Безопасность**: Все эндпоинты требуют аутентификации через JWT токен.

5. **Масштабируемость**: Можно увеличивать количество Celery workers для обработки большего количества задач.

### Тестирование

Для проверки корректности реализации создан тестовый скрипт `test_celery_integration.py`:

```bash
python test_celery_integration.py
```

Скрипт проверяет:
- Корректность импортов
- Конфигурацию Celery
- Регистрацию задач
- Наличие всех необходимых эндпоинтов в FastAPI
