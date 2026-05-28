# 🌀 HidConverter

**Универсальный асинхронный медиа-комбайн** — конвертируйте всё, что угодно, прямо из браузера.  
Изображения, аудио, видео, документы, QR-коды, хэши — единый API + PWA-интерфейс.

---

## Ключевые возможности

### 🔄 Конвертация файлов
| Категория | Входные форматы | Выходные форматы |
|-----------|----------------|------------------|
| **Изображения** | PNG, JPG, WEBP, BMP, GIF, ICO | PNG → JPG, WEBP, BMP, GIF, ICO и все взаимные комбинации |
| **Аудио** | MP3, WAV, OGG, FLAC, M4A, AAC | Полная взаимная конвертация с настройкой битрейта |
| **Видео** | MP4, AVI, MKV, MOV, WEBM | Взаимная конвертация + извлечение аудиодорожки в MP3 |
| **Документы** | PDF, DOCX, TXT, MD, XLSX, CSV | PDF ↔ DOCX, PDF → TXT, TXT/MD → PDF, XLSX → CSV/PDF |
| **Данные** | JSON, YAML, XML | Взаимная конвертация текстовых матриц |

### 📦 Пакетная обработка
- Загружайте несколько файлов одновременно
- Автоматическая упаковка результата в ZIP
- Индикатор прогресса загрузки по каждому файлу

### 🛡 Безопасность и приватность
- **Очистка EXIF-метаданных** — удаление GPS-координат, даты съёмки, модели устройства из изображений перед конвертацией
- **Хэширование** — вычисление MD5, SHA-1, SHA-256 для файлов и текста

### 📱 QR-коды
- **Генерация:** текст/URL → QR-код в PNG или SVG
- **Декодирование:** загрузите изображение с QR-кодом → получите текст

### 🌐 Сетевые утилиты
- **Конвертация по URL** — передайте прямую ссылку на файл, бэкенд скачает и сконвертирует
- **YouTube→MP3/WAV** — вставьте ссылку на YouTube, получите аудиодорожку в максимальном качестве

### ⌨️ Умный интерфейс
- **Ctrl+V из буфера обмена** — вставьте скриншот или скопированный текст, и они мгновенно появятся в списке файлов
- **Предпросмотр** — миниатюры для изображений и встроенный аудиоплеер прямо в списке файлов
- **PWA (Progressive Web App)** — установите как приложение на телефон или ПК, работает офлайн

### ⚙️ Тонкая настройка
- Качество сжатия (1–100 %)
- Битрейт аудио (128–320 kbps)
- Флаг очистки метаданных

---

## Быстрый старт

### Способ 1: Классический (через виртуальное окружение)

**Требования:** Python 3.10+, FFmpeg, Git

```bash
# 1. Клонируйте репозиторий
git clone https://github.com/your-username/hidconverter.git
cd hidconverter

# 2. Создайте и активируйте виртуальное окружение
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate

# 3. Установите зависимости
pip install -r requirements.txt

# 4. Установите FFmpeg (если ещё не установлен)
# Windows: winget install ffmpeg  или  https://ffmpeg.org/
# macOS:   brew install ffmpeg
# Linux:   sudo apt install ffmpeg

# 5. Запустите сервер
uvicorn backend.main:app --reload --port 8000
```

Откройте **http://localhost:8000** в браузере.  
Swagger-документация: **http://localhost:8000/docs**

### Способ 2: Современный (через Docker)

**Требования:** Docker, Docker Compose

```bash
# Одна команда — и всё работает
docker-compose up --build
```

Откройте **http://localhost:8000**.  
FFmpeg и все системные зависимости уже установлены внутри контейнера.

---

## API Endpoints

| Метод | Эндпоинт | Описание |
|-------|----------|----------|
| `GET` | `/api/categories` | Список категорий и поддерживаемых расширений |
| `GET` | `/api/formats` | Матрица конвертаций «из → в» для каждой категории |
| `POST` | `/api/convert` | Конвертация загруженных файлов |
| `POST` | `/api/convert-url` | Скачивание файла по URL и конвертация |
| `POST` | `/api/hash` | Хэширование файла или текста (MD5, SHA-1, SHA-256) |
| `POST` | `/api/qr/encode` | Генерация QR-кода из текста |
| `POST` | `/api/qr/decode` | Декодирование QR-кода из изображения |
| `POST` | `/api/metadata/clean` | Очистка EXIF-метаданных изображения |

---

## Структура проекта

```
HidConverter/
├── backend/
│   ├── main.py                     # FastAPI-приложение (все эндпоинты)
│   ├── utils.py                    # Валидация, разрешённые расширения, очистка uploads
│   └── converters/
│       ├── __init__.py             # Экспорт всех конвертеров
│       ├── base.py                 # Абстрактный базовый класс конвертера
│       ├── image_converter.py      # Изображения (Pillow)
│       ├── audio_converter.py      # Аудио (FFmpeg)
│       ├── video_converter.py      # Видео (FFmpeg)
│       ├── document_converter.py   # Документы (python-docx, openpyxl, fpdf2, pdfplumber)
│       ├── data_converter.py       # Текстовые матрицы (PyYAML, xmltodict)
│       ├── hash_converter.py       # Хэши (hashlib)
│       ├── metadata_cleaner.py     # Очистка EXIF/GPS из изображений
│       ├── qr_converter.py         # Генерация и декодирование QR-кодов
│       └── network_converter.py    # Скачивание по URL, YouTube → аудио
├── frontend/
│   ├── index.html                  # PWA-интерфейс
│   ├── style.css                   # Тёмная тема, адаптивная вёрстка
│   ├── app.js                      # Вся клиентская логика
│   ├── manifest.json               # PWA-манифест
│   ├── sw.js                       # Service Worker (кэширование, офлайн)
│   └── icon.svg                    # Иконка приложения
├── uploads/                        # Временные файлы (автоматическая очистка)
├── Dockerfile                      # Production-контейнер
├── docker-compose.yml              # Оркестрация одной командой
├── requirements.txt                # Python-зависимости
└── .gitignore
```

---

## Технологический стек

- **Backend:** Python 3.12, FastAPI, Uvicorn
- **Медиа:** FFmpeg, Pillow, yt-dlp
- **Документы:** python-docx, openpyxl, pdfplumber, fpdf2
- **Данные:** PyYAML, xmltodict, Markdown
- **QR:** qrcode, pyzbar
- **Фронтенд:** Vanilla JS, CSS (темная тема), PWA (Service Worker + Manifest)
- **Инфраструктура:** Docker, Docker Compose

---

## Разработка

### Форматирование кода

Автоматическое форматирование всего проекта (black + isort + ruff):

```bash
ruff check . --fix && ruff format . && isort .
```

### Проверка качества (lint) без изменений

Запуск линтера перед коммитом (без записи в файлы):

```bash
ruff check .
ruff format . --check
isort . --check-only
```

### Тесты со стилем

Запуск pytest автоматически выполняет `ruff` благодаря плагину `pytest-ruff` и конфигу `addopts = --ruff`:

```bash
pytest
```

---

## Лицензия

MIT
