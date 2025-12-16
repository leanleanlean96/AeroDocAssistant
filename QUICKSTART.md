# Быстрый старт AeroDoc Assistant

## Предварительные требования

- Python 3.12+
- Node.js и npm
- YandexGPT API ключ и Catalog ID

## Установка

### Backend

1. Перейдите в директорию backend:
```bash
cd backend
```

2. Установите зависимости:
```bash
pip install -r requirements.txt
```

3. Создайте файл `env/llm.env` на основе `env/llm.env.example`:
```bash
cp env/llm.env.example env/llm.env
```

4. Заполните `env/llm.env` своими данными:
```env
YANDEX_API_KEY=ваш_api_ключ
CATALOG_ID=ваш_catalog_id
```

### Frontend

1. Перейдите в директорию frontend:
```bash
cd frontend
```

2. Установите зависимости:
```bash
npm install
```

3. (Опционально) Создайте файл `.env` для настройки URL API:
```env
REACT_APP_API_URL=http://localhost:8000
```

## Запуск

### Backend

Из корневой директории проекта:
```bash
npm run start:backend
```

Или напрямую:
```bash
cd backend/src
python main.py
```

API будет доступен по адресу: http://localhost:8000

Документация API:
- Swagger: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### Frontend

Из корневой директории проекта:
```bash
npm run start:frontend
```

Или напрямую:
```bash
cd frontend
npm start
```

Фронтенд будет доступен по адресу: http://localhost:3000

## Первоначальная загрузка данных

После запуска backend, загрузите документы из датасета:

1. Через API:
```bash
curl -X POST http://localhost:8000/upload/dataset
```

2. Или через Swagger UI: http://localhost:8000/docs

## Использование

1. Откройте фронтенд в браузере: http://localhost:3000
2. Загрузите документы через кнопку "PDF" в правом нижнем углу
3. Задайте вопрос в поле ввода
4. Получите ответ с цитированием источников

## Структура проекта

```
AeroDocAssistant/
├── backend/              # FastAPI бэкенд
│   ├── src/
│   │   ├── main.py      # Точка входа
│   │   ├── config.py    # Конфигурация
│   │   ├── models/      # Pydantic модели
│   │   ├── routers/     # API эндпоинты
│   │   ├── services/    # Бизнес-логика
│   │   └── utils/       # Утилиты
│   └── env/             # Переменные окружения
├── frontend/            # React фронтенд
│   └── src/
│       └── App.tsx      # Главный компонент
└── dataset/             # Датасет с документами
```

## API Эндпоинты

- `POST /upload` - загрузка документов
- `POST /upload/dataset` - загрузка всего датасета
- `POST /search` - семантический поиск
- `POST /ask` - вопрос-ответ
- `GET /graph/{doc_id}` - граф связей документа
- `GET /graph` - весь граф
- `POST /validate` - проверка актуальности и противоречий

Подробная документация: http://localhost:8000/docs

## Устранение неполадок

### Backend не запускается

1. Проверьте, что все зависимости установлены: `pip install -r requirements.txt`
2. Проверьте наличие файла `env/llm.env` с правильными ключами
3. Убедитесь, что порт 8000 свободен

### Frontend не подключается к API

1. Проверьте, что backend запущен на порту 8000
2. Проверьте настройки CORS в `backend/src/config.py`
3. Убедитесь, что переменная `REACT_APP_API_URL` установлена правильно

### Ошибки при загрузке документов

1. Убедитесь, что формат файлов поддерживается (PDF, DOCX, JSON, XML)
2. Проверьте логи backend для деталей ошибки
3. Убедитесь, что есть достаточно места на диске

## Дополнительная информация

Подробная документация:
- Backend: `backend/README.md`
- Frontend: `frontend/README.md`
- Dataset: `dataset/README.md`

