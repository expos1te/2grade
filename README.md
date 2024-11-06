# HR Bot для Telegram

Бот помогает управлять резюме, добавлять их через Telegram и автоматически выгружать в Google Sheets для удобного хранения и анализа.

## Установка

### Предварительные требования

- Python 3.10
- Установленный `pip3.10`
- Доступ к Google Sheets API (для экспорта данных)

### Шаги установки

1. Клонируйте репозиторий:

    ```bash
    git clone https://github.com/expos1te/2grade.git
    cd 2grade
    ```

2. Создайте виртуальное окружение (рекомендуется):

    ```bash
    python3.10 -m venv venv
    source venv/bin/activate  # для Linux и macOS
    .\venv\Scripts\activate   # для Windows
    ```

3. Установите зависимости:

    ```bash
    pip3.10 install -r requirements.txt
    ```

4. Настройте конфигурацию:
    - Создайте файл `config.py` в корне проекта.
    - Укажите в нем токен вашего Telegram бота (`TOKEN`) и параметры для Google Sheets API.

5. Запустите бота:

    ```bash
    python3.10 main.py
    ```

## Основные команды

- `/start` — Добавление нового резюме.
