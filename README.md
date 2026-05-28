# HidConverter

Универсальный веб-конвертер файлов. Загружайте файлы через браузер и конвертируйте их в нужный формат.

## Возможности

- **Изображения:** PNG, JPG, WEBP, BMP, GIF, ICO (взаимная конвертация + оптимизация)
- **Аудио:** MP3, WAV, OGG, FLAC, M4A, AAC
- **Видео:** MP4, AVI, MKV, MOV, WEBM (+ извлечение аудио в MP3)
- **Документы:** PDF ↔ DOCX, PDF → TXT, TXT/MD → PDF, XLSX → CSV/PDF

## Быстрый старт

### 1. Установка зависимостей

```bash
pip install -r requirements.txt
```

Также требуется установить **FFmpeg** (для аудио/видео конвертации):
- **Windows:** `winget install ffmpeg` или скачайте с [ffmpeg.org](https://ffmpeg.org/)
- **macOS:** `brew install ffmpeg`
- **Linux:** `sudo apt install ffmpeg`

### 2. Запуск бэкенда

```bash
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

Swagger-документация: http://localhost:8000/docs

### 3. Открыть фронтенд

Откройте `frontend/index.html` в браузере (или через Live Server).

## API

| Метод | Эндпоинт | Описание |
|-------|----------|----------|
| GET | `/api/categories` | Список категорий и расширений |
| GET | `/api/formats` | Матрица поддерживаемых конвертаций |
| POST | `/api/convert` | Конвертировать файл (multipart: `file` + `target_format`) |

## Структура проекта

```
HidConverter/
├── backend/
│   ├── __init__.py
│   ├── main.py            # FastAPI приложение
│   ├── utils.py           # Валидация, очистка
│   └── converters/
│       ├── __init__.py
│       ├── base.py        # Абстрактный базовый класс
│       ├── image_converter.py
│       ├── audio_converter.py
│       ├── video_converter.py
│       └── document_converter.py
├── frontend/
│   ├── index.html
│   ├── style.css
│   └── app.js
├── uploads/               # Временные файлы (автоочистка)
├── requirements.txt
└── .gitignore
```

## Добавление нового формата

1. Добавьте расширение в `ALLOWED_EXTENSIONS` и `FILE_CATEGORIES` в `backend/utils.py`
2. Пропишите конвертацию в соответствующем конвертере (или создайте новый)
3. Обновите матрицу `SUPPORTED` в конвертере
