# AI-WebSite
Project work
1.Убедитесь, что у вас установлен Python версии 3.8 или выше. Проверить можно командой:  python –version
2. Клонируйте этот репозиторий(в будущем) или скачайте код.
3. Перейдите в папку проекта: cd путь_к_папке_проекта
4. Создайте виртуальное окружение для изоляции зависимостей: python -m venv venv
5. Активируйте виртуальное окружение:
   - Для Windows:
     venv\Scripts\activate
   - Для macOS/Linux:
     source venv/bin/activate
6. Установите зависимости из файла `requirements.txt`: pip install -r requirements.txt, также установите LibreOffice с официального сайта и запустите файл req.py 
Запуск
1. Убедитесь, что виртуальное окружение активировано (см. шаг 5 выше).
2. Запустите сервер с использованием Hypercorn: hypercorn app:app
   Здесь `app:app` — путь к вашему приложению Quart (замените на соответствующий путь, если ваше приложение называется иначе).
3. Откройте ваш веб-браузер и перейдите по адресу:  localhost:5000
- `requirements.txt`: Список зависимостей для проекта.
- `app.py` (или другой файл): Основной файл приложения Quart.
Зависимости
Проект использует следующие библиотеки:
- Quart: Для создания веб-приложений.
- databases[sqlite]: Асинхронная работа с SQLite.
 - aiohttp: Для выполнения асинхронных HTTP-запросов.
- Hypercorn: Сервер для запуска приложения.
