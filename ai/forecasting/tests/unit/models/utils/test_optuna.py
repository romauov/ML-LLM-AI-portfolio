import unittest
import pandas as pd

from app.models.utils.optuna import mape_by_category_and_folds


class TestOptunaUtils(unittest.TestCase):

    def test_mape_by_category_and_folds_single_category(self):
        """Test MAPE calculation for single category across folds"""
        # Create sample forecast data for one fold
        forecast_fold = pd.DataFrame({
            'ds': pd.date_range(start='2023-01-01', periods=5, freq='W-MON'),
            'y': [100.0, 105.0, 110.0, 108.0, 112.0],
            'pred': [101.0, 104.0, 111.0, 107.0, 113.0],
            'ID': ['A'] * 5
        })

        forecasting_folds = [forecast_fold]

        result = mape_by_category_and_folds(forecasting_folds)

        # Round the result to 2 decimal places for comparison
        rounded_result = {k: round(v, 2) for k, v in result.items()}

        expected_result = {'A': 0.94}
        self.assertEqual(rounded_result, expected_result)

    def test_mape_by_category_and_folds_multiple_categories(self):
        """Test MAPE calculation for multiple categories across folds"""
        # Create sample forecast data with multiple categories
        forecast_fold = pd.DataFrame({
            'ds': pd.date_range(start='2023-01-01', periods=6, freq='W-MON').tolist(),
            'y': [100.0, 105.0, 110.0, 200.0, 205.0, 210.0],
            'pred': [101.0, 104.0, 111.0, 201.0, 204.0, 211.0],
            'ID': ['A'] * 3 + ['B'] * 3
        })

        forecasting_folds = [forecast_fold]

        result = mape_by_category_and_folds(forecasting_folds)

        # Round the result to 2 decimal places for comparison
        rounded_result = {k: round(v, 2) for k, v in result.items()}

        expected_result = {'A': 0.95, 'B': 0.49}
        self.assertEqual(rounded_result, expected_result)

    def test_mape_by_category_and_folds_multiple_folds(self):
        """Test MAPE calculation across multiple folds"""
        # Create sample forecast data for multiple folds
        forecast_fold_1 = pd.DataFrame({
            'ds': pd.date_range(start='2023-01-01', periods=3, freq='W-MON'),
            'y': [100.0, 105.0, 110.0],
            'pred': [101.0, 104.0, 111.0],
            'ID': ['A'] * 3
        })

        forecast_fold_2 = pd.DataFrame({
            'ds': pd.date_range(start='2023-02-01', periods=3, freq='W-MON'),
            'y': [102.0, 107.0, 112.0],
            'pred': [103.0, 106.0, 113.0],
            'ID': ['A'] * 3
        })

        forecasting_folds = [forecast_fold_1, forecast_fold_2]

        result = mape_by_category_and_folds(forecasting_folds)

        # Round the result to 2 decimal places for comparison
        rounded_result = {k: round(v, 2) for k, v in result.items()}

        expected_result = {'A': 0.94}
        self.assertEqual(rounded_result, expected_result)

    def test_mape_by_category_and_folds_perfect_predictions(self):
        """Test MAPE calculation with perfect predictions (should be 0)"""
        # Create sample forecast data with perfect predictions
        forecast_fold = pd.DataFrame({
            'ds': pd.date_range(start='2023-01-01', periods=3, freq='W-MON'),
            'y': [100.0, 105.0, 110.0],
            'pred': [100.0, 105.0, 110.0],  # Perfect predictions
            'ID': ['A'] * 3
        })

        forecasting_folds = [forecast_fold]

        result = mape_by_category_and_folds(forecasting_folds)

        # With perfect predictions, MAPE should be exactly 0.0
        expected_result = {'A': 0.0}
        self.assertEqual(result, expected_result)


if __name__ == '__main__':
    unittest.main()
