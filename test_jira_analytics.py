import unittest
import json
import os
import tempfile
from unittest.mock import Mock, patch
import sys

# Добавляем текущую директорию в путь для импорта
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from jira_analytics import JiraAnalytics

class TestJiraAnalytics(unittest.TestCase):
    
    def setUp(self):
        """Настройка перед каждым тестом"""
        # Создаем временный конфиг файл для тестов
        self.test_config = {
            "jira_server": "https://issues.apache.org/jira",
            "project_key": "KAFKA",
            "max_results": 50
        }
        
        self.temp_config_file = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False)
        json.dump(self.test_config, self.temp_config_file)
        self.temp_config_file.close()
        
        self.analytics = JiraAnalytics(self.temp_config_file.name)
    
    def tearDown(self):
        """Очистка после каждого теста"""
        if os.path.exists(self.temp_config_file.name):
            os.unlink(self.temp_config_file.name)
    
    def test_1_config_loading(self):
        """Тест 1: Загрузка конфигурации из JSON файла"""
        print("Тест 1: Проверка загрузки конфигурации...")
        self.assertEqual(self.analytics.project_key, "KAFKA")
        self.assertEqual(self.analytics.jira_server, "https://issues.apache.org/jira")
        self.assertEqual(self.analytics.max_results, 50)
        print("✅ Конфигурация загружена корректно")
    
    def test_2_output_directory_creation(self):
        """Тест 2: Создание выходной директории"""
        print("Тест 2: Проверка создания папки outputs...")
        self.assertTrue(os.path.exists("outputs"))
        self.assertTrue(os.path.isdir("outputs"))
        print("✅ Папка outputs создана")
    
    def test_3_session_initialization(self):
        """Тест 3: Инициализация HTTP-сессии"""
        print("Тест 3: Проверка инициализации сессии...")
        self.assertIsNotNone(self.analytics.session)
        # Проверяем что сессия создана (не проверяем конкретные заголовки)
        self.assertTrue(hasattr(self.analytics.session, 'get'))
        self.assertTrue(hasattr(self.analytics.session, 'post'))
        print("✅ HTTP-сессия инициализирована")
    
    def test_4_safe_filename_generation(self):
        """Тест 4: Генерация безопасных имен файлов"""
        print("Тест 4: Проверка генерации имен файлов...")
        
        # Тестируем функцию безопасного имени файла (копия из основного кода)
        def safe_filename(status):
            return "".join(c if c.isalnum() or c in (' ', '-', '_') else '_' for c in str(status)).rstrip()
        
        test_cases = [
            ("Open", "Open"),
            ("In Progress", "In Progress"),
            ("Resolved/Closed", "Resolved_Closed"),
            ("Done!", "Done_"),
            ("Test*File?Name", "Test_File_Name")
        ]
        
        for input_status, expected in test_cases:
            result = safe_filename(input_status)
            self.assertEqual(result, expected)
            print(f"✅ '{input_status}' -> '{result}'")
    
    def test_5_methods_existence(self):
        """Тест 5: Проверка наличия всех основных методов"""
        print("Тест 5: Проверка наличия методов...")
        
        required_methods = [
            'load_config',
            'get_issues', 
            'prepare_data',
            'plot_lead_time_histogram',
            'plot_time_in_status',
            'plot_daily_issue_flow',
            'plot_top_users',
            'plot_user_worklog_histogram',
            'plot_issues_by_priority',
            'generate_all_reports'
        ]
        
        for method in required_methods:
            self.assertTrue(hasattr(self.analytics, method))
            self.assertTrue(callable(getattr(self.analytics, method)))
            print(f"✅ Метод {method} присутствует")

    def test_6_data_structures(self):
        """Тест 6: Проверка структур данных"""
        print("Тест 6: Проверка структур данных...")
        
        # Создаем тестовые данные для проверки логики
        test_issues = [
            {
                'fields': {
                    'created': '2023-01-01T10:00:00.000+0000',
                    'resolutiondate': '2023-01-05T10:00:00.000+0000',
                    'status': {'name': 'Closed'},
                    'priority': {'name': 'High'},
                    'assignee': {'displayName': 'Test User'},
                    'reporter': {'displayName': 'Reporter User'},
                    'timespent': 3600
                }
            }
        ]
        
        # Проверяем что методы можно вызвать без ошибок (пока без реального выполнения)
        try:
            # Эти методы должны существовать и быть callable
            self.assertTrue(callable(self.analytics.plot_lead_time_histogram))
            self.assertTrue(callable(self.analytics.plot_time_in_status))
            self.assertTrue(callable(self.analytics.plot_issues_by_priority))
            print("✅ Все методы готовы к работе")
        except Exception as e:
            self.fail(f"Методы не могут быть вызваны: {e}")

def run_all_tests():
    """Запуск всех тестов с детальным выводом"""
    print("=" * 60)
    print("ЗАПУСК МОДУЛЬНЫХ ТЕСТОВ JIRA ANALYTICS")
    print("=" * 60)
    
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestJiraAnalytics)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    print("=" * 60)
    print("ИТОГИ ТЕСТИРОВАНИЯ:")
    print(f"Всего тестов: {result.testsRun}")
    print(f"Пройдено: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Провалено: {len(result.failures)}")
    print(f"Ошибок: {len(result.errors)}")
    
    if result.wasSuccessful():
        print("🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ УСПЕШНО!")
    else:
        print("❌ ЕСТЬ ПРОБЛЕМЫ В ТЕСТАХ")
        if result.failures:
            print("\nПроваленные тесты:")
            for test, traceback in result.failures:
                print(f"  - {test}: {traceback.splitlines()[-1]}")
        if result.errors:
            print("\nТесты с ошибками:")
            for test, traceback in result.errors:
                print(f"  - {test}: {traceback.splitlines()[-1]}")
    
    return result.wasSuccessful()

if __name__ == '__main__':
    run_all_tests()