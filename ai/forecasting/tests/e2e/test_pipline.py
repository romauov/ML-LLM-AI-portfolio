import unittest
from unittest.mock import patch
import pandas as pd
from omegaconf import OmegaConf

from app.predictor.predictor import predict_pipline
from config.configs import Config


class TestPredictPipeline(unittest.TestCase):
    """Тестирование функции predict_pipline"""

    def setUp(self):
        """Подготовка тестовых данных"""
        # Загрузка тестовых данных из CSV файла
        self.df_prepared = pd.read_csv('tests/test_data/df_prepared.csv')

        # Загрузка конфигурации
        cfg_dict = OmegaConf.to_container(OmegaConf.load('tests/test_config.yaml'), resolve=True)
        self.config = Config(**cfg_dict)

    def test_predict_pipeline_with_mocked_functions(self):
        """Тестирование функции predict_pipline с замоканными функциями"""
        # Подготовим тестовые данные с правильным форматом даты
        df_test = self.df_prepared.copy()
        df_test['ds'] = pd.to_datetime(df_test['ds'])

        with patch('app.predictor.predictor.get_data_by_config') as mock_get_data_by_config, \
                patch('app.database.db.save_forecasting') as mock_save_forecasting:
            # Настройка мока для возвращения тестовых данных
            mock_get_data_by_config.return_value = df_test

            # Вызов тестируемой функции
            result = predict_pipline(cfg=self.config, save_db=False)

            # Проверка, что моки были вызваны
            mock_get_data_by_config.assert_called_once()
            # save_forecasting не должен быть вызван, так как возвращается результат
            mock_save_forecasting.assert_not_called()

            # Проверка результата
            self.assertIsInstance(result, pd.DataFrame)
            self.assertFalse(result.empty)

            # Проверка, что результат содержит ожидаемые колонки
            expected_columns = ['date', 'ID', 'price', 'best_model', 'mape']
            for col in expected_columns:
                self.assertIn(col, result.columns)


if __name__ == '__main__':
    unittest.main()
