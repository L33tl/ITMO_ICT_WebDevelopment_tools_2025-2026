# Лабораторная работа 3: Упаковка FastAPI приложения в Docker, Работа с источниками данных и Очереди

## Цель работы
Упаковка FastAPI приложения, базы данных и парсера данных в Docker контейнеры с созданием оркестрации сервисов через Docker Compose.

## Задачи
1. Создание FastAPI приложения (уже выполнено)
2. Создание базы данных (уже выполнено)
3. Создание парсера данных (уже выполнено)
4. Реализация возможности вызова парсера по HTTP
5. Разработка Dockerfile для упаковки приложения
6. Создание Docker Compose файла для оркестрации сервисов

## Выполнение работы

### 1. Анализ существующей структуры проекта
Перед началом работы был проведен анализ существующего проекта:
- **main.py** - основное FastAPI приложение для управления хакатоном
- **models.py** - модели данных SQLModel
- **connection.py** - подключение к базе данных PostgreSQL
- **auth.py** - аутентификация и авторизация
- **parser_app.py** - новое приложение для парсера (создано в рамках работы)
- **lab2/** - существующие реализации парсеров (sequential, async, multiprocessing)

### 2. Реализация HTTP-интерфейса для парсера
Создано отдельное FastAPI приложение `parser_app.py` с следующими endpoint'ами:

#### Основные endpoint'ы:
- `GET /` - информация о API
- `POST /parse?url=<url>` - парсинг указанного URL
- `GET /health` - проверка работоспособности
- `GET /stats` - статистика парсинга

#### Пример использования:
```bash
curl -X POST "http://localhost:8001/parse?url=https://example.com"
```

#### Реализация парсера:
```python
def parse_and_save(url: str) -> Dict[str, Any]:
    """Функция парсинга URL с сохранением в SQLite базу"""
    response = requests.get(url, timeout=10)
    soup = BeautifulSoup(response.text, 'html.parser')
    title = soup.title.string if soup.title else "No title"
    # Сохранение в базу данных web_scraping.db
```

### 3. Создание Dockerfile
Разработан многостадийный Dockerfile для упаковки приложения:

```dockerfile
FROM python:3.11-slim as builder
# Установка зависимостей и компиляция
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

FROM python:3.11-slim
# Копирование зависимостей из builder
COPY --from=builder /root/.local /root/.local
COPY . .
# Создание non-root пользователя для безопасности
USER appuser
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
```

#### Зависимости (requirements.txt):
```
fastapi==0.104.1
uvicorn[standard]==0.24.0
sqlmodel==0.0.14
sqlalchemy==2.0.23
pydantic==2.5.0
requests==2.31.0
beautifulsoup4==4.12.2
aiohttp==3.9.1
psycopg2-binary==2.9.9
alembic==1.12.1
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
```

### 4. Создание Docker Compose конфигурации

```yaml
services:
  postgres:
    image: postgres:16
    ports: ["5432:5432"]
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres52
      POSTGRES_DB: hackaton_db
    volumes:
      - postgres_data:/var/lib/postgresql/data

  fastapi-app:
    build: .
    ports: ["8000:8000"]
    environment:
      DATABASE_URL: postgresql://postgres:postgres52@postgres:5432/hackaton_db
    depends_on:
      - postgres
    command: uvicorn main:app --host 0.0.0.0 --port 8000 --reload

  parser-app:
    build: .
    ports: ["8001:8001"]
    depends_on:
      - postgres
    command: uvicorn parser_app:app --host 0.0.0.0 --port 8001 --reload

volumes:
  postgres_data:
```

### 5. Архитектура решения
```
┌─────────────────────────────────────────────────────────┐
│                    Docker Compose                        │
├──────────────┬────────────────┬─────────────────────────┤
│  PostgreSQL  │  FastAPI App   │     Parser App          │
│  (postgres)  │  (port 8000)   │     (port 8001)         │
│              │                │                         │
│  - База      │  - Основное    │  - HTTP интерфейс       │
│    данных    │    приложение  │    для парсера          │
│  - Постгрес  │  - API         │  - Парсинг веб-страниц  │
│   16         │    хакатона    │  - SQLite для результатов│
└──────────────┴────────────────┴─────────────────────────┘
```

## Инструкция по запуску

### 1. Предварительные требования
- Установленный Docker и Docker Compose
- 2 ГБ свободной памяти
- Порты 8000, 8001, 5432 свободны

### 2. Запуск приложения
```bash
# Клонирование репозитория (если нужно)
git clone <repository-url>
cd ITMO_ICT_WebDevelopment_tools_2025-2026

# Запуск всех сервисов
docker-compose up --build

# Запуск в фоновом режиме
docker-compose up -d
```

### 3. Проверка работоспособности
```bash
# Проверка основного приложения
curl http://localhost:8000/

# Проверка парсера
curl http://localhost:8001/

# Тестирование парсинга
curl -X POST "http://localhost:8001/parse?url=https://example.com"

# Проверка статистики
curl http://localhost:8001/stats
```

### 4. Остановка приложения
```bash
# Остановка с удалением контейнеров
docker-compose down

# Остановка с удалением контейнеров и volumes
docker-compose down -v
```

## Тестирование

### 1. Тестирование Docker образа
```bash
# Сборка образа
docker build -t fastapi-app .

# Запуск контейнера
docker run -p 8000:8000 fastapi-app
```

### 2. Тестирование парсера
```python
import requests

# Тест парсинга
response = requests.post(
    "http://localhost:8001/parse",
    params={"url": "https://python.org"}
)
print(response.json())
```

### 3. Проверка связи между сервисами
```bash
# Проверка доступности PostgreSQL из контейнера
docker-compose exec fastapi-app ping postgres

# Проверка логов
docker-compose logs -f fastapi-app
docker-compose logs -f parser-app
```
