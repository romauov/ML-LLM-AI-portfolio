import unittest
from unittest.mock import patch
import pandas as pd

from app.data.handlers.from_database import get_data_from_database
from omegaconf import OmegaConf
from config.configs import Config


class TestGetDataFromDatabase(unittest.TestCase):
    """Тестирование функции get_data_from_database"""

    def setUp(self):
        """Подготовка тестовых данных"""
        # Загрузка тестовых данных из CSV файлов
        self.df_meat = pd.read_csv('tests/test_data/df_meat.csv')
        self.df_fish = pd.read_csv('tests/test_data/df_fish.csv')
        self.df_caviar = pd.read_csv('tests/test_data/df_caviar.csv')
        self.df_seafood = pd.read_csv('tests/test_data/df_seafood.csv')
        self.df_shrimp = pd.read_csv('tests/test_data/df_shrimp.csv')
        self.df_semiprocessed = pd.read_csv('tests/test_data/df_semiprocessed.csv')

        # Загрузка ожидаемого результата
        self.expected_result = pd.read_csv('tests/test_data/df_prepared.csv', index_col=0)

        # Загрузка конфигурации
        cfg_dict = OmegaConf.to_container(OmegaConf.load('tests/test_config.yaml'), resolve=True)
        self.config = Config(**cfg_dict)

    def test_get_data_from_database_with_mocked_functions(self):
        """Тестирование функции get_data_from_database"""

        # Создаем мок для get_seafood_data, который будет возвращать разные данные в зависимости от products_type
        def mock_get_seafood_data_side_effect(products_type, sql_condition, date_from, date_to, db_connect=None):
            if products_type.value == 'Морепродукты':
                df_result = self.df_seafood.copy()
            elif products_type.value == 'Икра':
                df_result = self.df_caviar.copy()
            elif products_type.value == 'Рыба':
                df_result = self.df_fish.copy()
            elif products_type.value == 'Креветки':
                df_result = self.df_shrimp.copy()
            elif products_type.value == 'Полуфабрикаты':
                df_result = self.df_semiprocessed.copy()
            else:
                raise ValueError(f"Unexpected products_type: {products_type}")

            df_result['date'] = pd.to_datetime(df_result['date'])

            return df_result

        # Создаем мок для get_meat_data
        def mock_get_meat_data_side_effect(sql_condition, date_from, date_to, db_connect=None):
            df_result = self.df_meat.copy()
            df_result['date'] = pd.to_datetime(df_result['date'])
            return df_result

        # Мокируем функции по месту их использования (в модуле, где они импортируются)
        with patch('app.data.handlers.from_database.get_meat_data', side_effect=mock_get_meat_data_side_effect), \
                patch('app.data.handlers.from_database.get_seafood_data',
                      side_effect=mock_get_seafood_data_side_effect):

            # Вызов тестируемой функции
            date_from = '2024-07-01'
            date_to = '2026-02-02'
            result = get_data_from_database(date_from=date_from, date_to=date_to, cfg=self.config)

            # Проверка результата
            self.assertIsInstance(result, pd.DataFrame)
            self.assertFalse(result.empty)

            # Проверка, что результат содержит ожидаемые колонки
            expected_columns = ['ID', 'ds', 'y']
            for col in expected_columns:
                self.assertIn(col, result.columns)

            # Проверка, что количество строк соответствует ожидаемому
            self.assertEqual(len(result), len(self.expected_result))

            # # Преобразуем колонку ds в обоих датафреймах к одному формату для сравнения
            result_ = result.copy()
            expected_ = self.expected_result.copy()

            # Преобразуем ds в строковый формат в обоих датафреймах
            result_['ds'] = pd.to_datetime(result_['ds']).dt.strftime('%Y-%m-%d')
            expected_['ds'] = pd.to_datetime(expected_['ds']).dt.strftime('%Y-%m-%d')

            pd.testing.assert_frame_equal(
                result_,
                expected_,
                check_dtype=False,
                rtol=0.05  # числовые значение отличающиеся друг от друга не более чем на 5% считаются, как одинаковые
            )


if __name__ == '__main__':
    unittest.main()
