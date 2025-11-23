@echo off
chcp 65001 > nul
echo Запуск JIRA Analytics для проекта KAFKA...


py --version > nul 2>&1
if errorlevel 1 (
    echo Ошибка: Python не найден! Используйте команду 'py'
    pause
    exit /b 1
)


if not exist "venv" (
    echo Создание виртуального окружения...
    py -m venv venv
)


echo Активация виртуального окружения...
call venv\Scripts\activate.bat


echo Установка зависимостей...
py -m pip install -r requirements.txt


echo Запуск анализа...
py jira_analytics.py

echo.
echo Анализ завершен. Проверьте папку 'outputs' для просмотра графиков.
pause