# Backend API — Documentation

Этот backend — REST API сервис на **Flask + PostgreSQL**.  
Ниже описаны все маршруты, параметры и структура данных.

---

## Стек
- Python + Flask  
- PostgreSQL + psycopg2  
- .env (переменная DATABASE_URL)

---

## Установка и запуск

### 1. Установка зависимостей
pip install -r requirements.txt

### 2. Создай файл .env:
DATABASE_URL=postgres://user:pass@host:port/dbname

### 3. Запуск:
python app.py

---

#  API Endpoints

## GET /
Проверка статуса API.

Пример ответа:
{
  "status": "ok",
  "routes": ["/services", "/subjects"]
}

---

# SUBJECTS

## GET /subjects
Список всех предметов.

Пример:
  {
    "category": "Программирование",
    "created_at": "Sun, 16 Nov 2025 21:59:39 GMT",
    "id": 7,
    "name": "Алгоритмы и структуры данных"
  },
  {
    "category": "Языки",
    "created_at": "Sun, 16 Nov 2025 21:59:39 GMT",
    "id": 31,
    "name": "Английский для IT"
  },
  ...

---

## GET /subjects/<id>
Получить предмет по ID.

OK:
{
  "category": "Технические",
  "created_at": "Sun, 16 Nov 2025 21:59:39 GMT",
  "id": 3,
  "name": "Сопротивление материалов"
}

404:
{ "error": "not found" }

---

## GET /subjects/by_name?name=...
Поиск предметов по имени (ILIKE).

Пример:
[
  {
    "category": "Программирование",
    "created_at": "Sun, 16 Nov 2025 21:59:39 GMT",
    "id": 12,
    "name": "Веб-разработка"
  }
]

---

# SERVICES

## GET /services
Получение объявлений с фильтрами и пагинацией.

Параметры:
- page — номер страницы
- per_page — количество элементов
- subject_id — фильтр по ID предмета
- subject_name — фильтр по названию предмета
- q — поиск по названию объявления

Пример ответа:
{
  "items": [],
  "page": 1,
  "per_page": 20,
  "total": 0,
  "pages": 0
}

---

## GET /services/<id>
Получить объявление по ID.

Пример:
{
  "id": 42,
  "title": "Репетитор по физике",
  "description": "Подготовка к ЕГЭ",
  "price": 1000,
  "education_format": "online",
  "contact_info": "@user",
  "subject_id": 2
}

---

## POST /services
Создать объявление.

Ожидаемый JSON:
{
  "title": "string",
  "description": "string",
  "contact_info": "string",
  "subject_id": 1,
  "price": 1000,
  "education_format": "online"
}

Ответ:
{
  "id": 55,
  "title": "...",
  "description": "...",
  "contact_info": "...",
  "subject_id": 1
}

---

## POST /services/bulk_import
Массовый импорт объявлений.

JSON:
{
  "services": [
    {
      "id": 1,
      "title": "Название",
      "description": "Описание",
      "price": 1000,
      "contact_info": "@user",
      "subject_id": 2,
      "created_at": "2024-01-01T00:00:00",
      "updated_at": "2024-01-02T00:00:00"
    }
  ]
}

Response:
{
  "imported": 10,
  "errors": []
}

---

# Структура таблиц

## subjects
- id (int)
- name (text)

## advertisements
- id (int)
- title (text)
- description (text)
- price (int)
- education_format (text)
- contact_info (text)
- subject_id (int)
- created_at (timestamp)
- updated_at (timestamp)

---

# Примечания
- Все ответы в JSON  
- Ошибки используют коды 400/404  
- Поиск ILIKE (регистронезависимый)  
- Пагинация: page + per_page
