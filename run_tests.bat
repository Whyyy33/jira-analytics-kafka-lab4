@echo off
chcp 65001 > nul
echo Запуск модульных тестов JIRA Analytics...

cd /d "%~dp0"

py --version > nul 2>&1
if errorlevel 1 (
    echo Ошибка: Python не найден!
    pause
    exit /b 1
)

echo.
echo ========================================
echo ЗАПУСК ТЕСТОВ
echo ========================================

py test_jira.py
set TEST_RESULT=%errorlevel%

echo.
echo ========================================
echo РЕЗУЛЬТАТЫ ТЕСТИРОВАНИЯ
echo ========================================
if %TEST_RESULT% equ 0 (
    echo  ВСЕ 5 ТЕСТОВ ПРОЙДЕНЫ УСПЕШНО!
    echo.
    echo Статус тестирования:
    echo - Тест 1: Загрузка конфигурации 
    echo - Тест 2: Создание JSON хранилища 
    echo - Тест 3: Создание выходной директории 
    echo - Тест 4: Инициализация HTTP-сессии 
    echo - Тест 5: Генерация безопасных имен файлов 
    echo.
    echo  МОДУЛЬНОЕ ТЕСТИРОВАНИЕ ЗАВЕРШЕНО УСПЕШНО!
) else (
    echo  НЕКОТОРЫЕ ТЕСТЫ НЕ ПРОЙДЕНЫ
    echo.
    echo Для деталей запустите: python test_jira.py
)

echo.
pause
