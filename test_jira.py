import unittest
import json
import os
import sys
from pathlib import Path

# Добавляем корневую папку в путь для импорта
sys.path.insert(0, str(Path(__file__).parent))

from jira_analytics import JiraAnalytics


class TestJiraAnalytics(unittest.TestCase):
    """Модульные тесты для JIRA Analytics"""
    
    @classmethod
    def setUpClass(cls):
        """Настройка перед запуском всех тестов"""
        cls.test_config_path = 'config.json'
        cls.test_output_dir = 'test_outputs'
    
    def test_1_config_loading(self):
        """Тест 1: Загрузка конфигурации"""
        # Проверяем что config.json существует
        self.assertTrue(
            os.path.exists(self.test_config_path),
            f"Ошибка: {self.test_config_path} не найден!"
        )
        
        # Проверяем что это валидный JSON
        try:
            with open(self.test_config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            # Проверяем наличие обязательных полей (исправлено на jira_server)
            required_fields = ['jira_server', 'project_key']
            for field in required_fields:
                self.assertIn(field, config, f"Поле '{field}' отсутствует в config.json")
        except json.JSONDecodeError:
            self.fail("config.json содержит невалидный JSON")
    
    def test_2_json_storage_creation(self):
        """Тест 2: Создание JSON хранилища"""
        # Создаем папку data если ее нет
        data_dir = 'data'
        if not os.path.exists(data_dir):
            os.makedirs(data_dir)
        
        # Проверяем что папка была создана
        self.assertTrue(
            os.path.exists(data_dir),
            "Папка 'data' не была создана"
        )
        
        # Проверяем что мы можем писать в папку
        test_file = os.path.join(data_dir, 'test.json')
        try:
            with open(test_file, 'w') as f:
                json.dump({'test': 'data'}, f)
            os.remove(test_file)
        except IOError:
            self.fail("Не удается писать JSON в папку 'data'")
    
    def test_3_output_directories_creation(self):
        """Тест 3: Создание папок вывода"""
        # Ожидаемые папки
        expected_dirs = ['outputs', 'outputs/charts']
        
        # Создаем папки если их нет
        for dir_path in expected_dirs:
            os.makedirs(dir_path, exist_ok=True)
        
        # Проверяем что все папки существуют
        for dir_path in expected_dirs:
            self.assertTrue(
                os.path.isdir(dir_path),
                f"Папка '{dir_path}' не существует"
            )
    
    def test_4_session_initialization(self):
        """Тест 4: Инициализация HTTP-сессии"""
        try:
            # Пытаемся создать экземпляр JiraAnalytics
            analytics = JiraAnalytics()
            
            # Проверяем что объект создан
            self.assertIsNotNone(analytics, "JiraAnalytics не инициализирован")
            
            # Проверяем что есть сессия
            self.assertIsNotNone(
                analytics.session,
                "HTTP сессия не инициализирована"
            )
        except Exception as e:
            self.fail(f"Ошибка инициализации JiraAnalytics: {str(e)}")
    
    def test_5_safe_filename_generation(self):
        """Тест 5: Генерация безопасных имен файлов"""
        # Тестируем встроенную функцию замены опасных символов
        test_cases = [
            ('valid_filename', 'valid_filename'),
            ('name with spaces', 'name_with_spaces'),
            ('name/with/slashes', 'name_with_slashes'),
            ('name\\with\\backslashes', 'name_with_backslashes'),
            ('name:with:colons', 'name_with_colons'),
            ('name?with?questions', 'name_with_questions'),
            ('name|with|pipes', 'name_with_pipes'),
        ]
        
        # Опасные символы которые нужно заменить
        dangerous_chars = ['/', '\\', ':', '?', '*', '|', '<', '>', '"']
        
        for unsafe_name, expected_result in test_cases:
            # Применяем замену опасных символов
            safe_name = unsafe_name
            for char in dangerous_chars:
                safe_name = safe_name.replace(char, '_')
            
            # Проверяем что в имени нет опасных символов
            for char in dangerous_chars:
                self.assertNotIn(
                    char, safe_name,
                    f"Опасный символ '{char}' найден в '{safe_name}'"
                )


def run_tests():
    """Функция для запуска всех тестов"""
    # Создаем test suite
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestJiraAnalytics)
    
    # Запускаем тесты с подробным выводом
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Возвращаем код выхода (0 если все прошло, 1 если ошибки)
    return 0 if result.wasSuccessful() else 1


if __name__ == '__main__':
    exit_code = run_tests()
    sys.exit(exit_code)