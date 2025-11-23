@echo off
chcp 65001 > nul
echo Установка библиотек для JIRA Analytics...
echo.
echo Устанавливаем requests...
py -m pip install requests
echo Устанавливаем pandas...
py -m pip install pandas
echo Устанавливаем matplotlib...
py -m pip install matplotlib
echo Устанавливаем seaborn...
py -m pip install seaborn
echo.
echo Проверяем установку...
py -c "import requests; print(' requests установлен')"
py -c "import pandas; print(' pandas установлен')" 
py -c "import matplotlib.pyplot; print(' matplotlib установлен')"
py -c "import seaborn; print(' seaborn установлен')"

echo.
echo ВСЕ БИБЛИОТЕКИ УСТАНОВЛЕНЫ!
echo Теперь запустите run_analytics.bat
pause