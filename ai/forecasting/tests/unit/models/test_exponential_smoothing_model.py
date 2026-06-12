import unittest
import pandas as pd

from app.models.exponential_smoothing_model import ExponentialSmoothingModel


class MockESModelConfig:
    """Mock class for exponential smoothing model configuration"""

    def __init__(self, seasonal_periods=7, trend="add", seasonal=None,
                 damped_trend=False, use_boxcox=False, freq="D"):
        self.seasonal_periods = seasonal_periods
        self.trend = trend
        self.seasonal = seasonal
        self.damped_trend = damped_trend
        self.use_boxcox = use_boxcox
        self.freq = freq

    def __iter__(self):
        # This allows converting to dict as expected by the model
        return iter([
            ('seasonal_periods', self.seasonal_periods),
            ('trend', self.trend),
            ('seasonal', self.seasonal),
            ('damped_trend', self.damped_trend),
            ('use_boxcox', self.use_boxcox),
            ('freq', self.freq)
        ])


class MockESTrainConfig:
    """Mock class for exponential smoothing train configuration"""

    def __init__(self, ew_lag=0):
        self.ew_lag = ew_lag


class TestExponentialSmoothingModel(unittest.TestCase):

    def setUp(self):
        """Set up test data with at least 2 unique IDs"""
        # Create sample data with 2 unique IDs
        dates = pd.date_range(start='2023-01-01', periods=10, freq='D')
        data = {
            'ds': dates.tolist() * 2,  # Repeat dates for 2 IDs
            'y': [10, 12, 13, 14, 15, 16, 17, 18, 19, 20] * 2,  # Sample values
            'ID': ['ID1'] * 10 + ['ID2'] * 10  # Two unique IDs
        }
        self.sample_df = pd.DataFrame(data)

        # Create model and train configurations
        self.model_cfg = MockESModelConfig()
        self.train_cfg = MockESTrainConfig()

    def test_initialization_with_valid_data(self):
        """Test initialization of ExponentialSmoothingModel with valid data"""
        model = ExponentialSmoothingModel(self.sample_df, self.model_cfg, self.train_cfg)

        self.assertIsInstance(model, ExponentialSmoothingModel)
        pd.testing.assert_frame_equal(model.df, self.sample_df)
        self.assertEqual(model.model_cfg, self.model_cfg)
        self.assertEqual(model.train_cfg, self.train_cfg)

    def test_predict_returns_correct_structure(self):
        """Test that predict method returns DataFrame with correct structure"""
        model = ExponentialSmoothingModel(self.sample_df, self.model_cfg, self.train_cfg)
        result = model.predict(n_preds=3)

        # Check that result is a DataFrame
        self.assertIsInstance(result, pd.DataFrame)

        # Check that result has the expected columns
        expected_columns = {'ds', 'pred', 'ID'}
        actual_columns = set(result.columns)
        self.assertEqual(expected_columns, actual_columns)

        # Check that result contains both IDs from input
        expected_ids = set(self.sample_df['ID'].unique())
        actual_ids = set(result['ID'].unique())
        self.assertEqual(expected_ids, actual_ids)

        # Check that prediction dates match the expected forecast horizon
        for cat in self.sample_df['ID'].unique():
            df_pred = result[result['ID'] == cat]
            pred_dates = sorted(df_pred['ds'].tolist())

            # Check that we have exactly n_preds predictions
            self.assertEqual(len(pred_dates), 3)

            # Check that the dates are consecutive (assuming daily frequency)
            for i in range(1, len(pred_dates)):
                expected_next_date = pred_dates[i - 1] + pd.Timedelta(days=1)
                self.assertEqual(pred_dates[i], expected_next_date)

    def test_predict_with_different_horizons(self):
        """Test predict method with different prediction horizons"""
        model = ExponentialSmoothingModel(self.sample_df, self.model_cfg, self.train_cfg)

        # Test with horizon of 1
        result_1 = model.predict(n_preds=1)
        self.assertEqual(len(result_1), 2)  # 1 prediction for each of 2 IDs

        # Test with horizon of 5
        result_5 = model.predict(n_preds=5)
        self.assertEqual(len(result_5), 10)  # 5 predictions for each of 2 IDs

    def test_predict_without_exponential_weighting(self):
        """Test predict method with ew_lag = 0 (no exponential weighting)"""
        model = ExponentialSmoothingModel(self.sample_df, self.model_cfg, MockESTrainConfig(ew_lag=0))
        result = model.predict(n_preds=2)

        # Check structure
        expected_columns = {'ds', 'pred', 'ID'}
        actual_columns = set(result.columns)
        self.assertEqual(expected_columns, actual_columns)

        # Check that both IDs are present
        expected_ids = set(self.sample_df['ID'].unique())
        actual_ids = set(result['ID'].unique())
        self.assertEqual(expected_ids, actual_ids)

    def test_predict_with_exponential_weighting(self):
        """Test predict method with ew_lag != 0 (with exponential weighting)"""
        model = ExponentialSmoothingModel(self.sample_df, self.model_cfg, MockESTrainConfig(ew_lag=2))
        result = model.predict(n_preds=2)

        # Check structure
        expected_columns = {'ds', 'pred', 'ID'}
        actual_columns = set(result.columns)
        self.assertEqual(expected_columns, actual_columns)

        # Check that both IDs are present
        expected_ids = set(self.sample_df['ID'].unique())
        actual_ids = set(result['ID'].unique())
        self.assertEqual(expected_ids, actual_ids)

    def test_predict_single_time_series(self):
        """Test with single time series (one unique ID)"""
        single_id_df = self.sample_df[self.sample_df['ID'] == 'ID1']
        model = ExponentialSmoothingModel(single_id_df, self.model_cfg, self.train_cfg)
        result = model.predict(n_preds=3)

        # Should have 3 predictions for the single ID
        self.assertEqual(len(result), 3)
        self.assertEqual(set(result['ID'].unique()), {'ID1'})

        # Validate dates for single time series
        pred_dates = sorted(result['ds'].tolist())

        self.assertEqual(len(pred_dates), 3)

        # Check that the dates are consecutive (assuming daily frequency)
        for i in range(1, len(pred_dates)):
            expected_next_date = pred_dates[i - 1] + pd.Timedelta(days=1)
            self.assertEqual(pred_dates[i], expected_next_date)

    def test_empty_dataframe_error_handling(self):
        """Test error handling with empty DataFrame"""
        empty_df = pd.DataFrame(columns=['ds', 'y', 'ID'])
        model = ExponentialSmoothingModel(empty_df, self.model_cfg, self.train_cfg)

        # Should handle gracefully or raise appropriate error
        with self.assertRaises(Exception):
            model.predict(n_preds=3)

    def test_insufficient_data_points(self):
        """Test with insufficient data points for prediction"""
        # Create a DataFrame with only one data point per ID
        minimal_data = {
            'ds': [pd.Timestamp('2023-01-01'), pd.Timestamp('2023-01-02')],
            'y': [10, 15],
            'ID': ['ID1', 'ID2']
        }
        minimal_df = pd.DataFrame(minimal_data)
        model = ExponentialSmoothingModel(minimal_df, self.model_cfg, self.train_cfg)

        with self.assertRaises(IndexError):
            model.predict(n_preds=3)

    def test_negative_prediction_horizon(self):
        """Test predict method with negative n_preds value"""
        model = ExponentialSmoothingModel(self.sample_df, self.model_cfg, self.train_cfg)

        with self.assertRaises(ValueError):
            model.predict(n_preds=-1)

    def test_missing_required_columns(self):
        """Test predict method with missing required columns"""
        # Create DataFrame without 'y' column
        incomplete_df = self.sample_df.drop(columns=['y'])
        model = ExponentialSmoothingModel(incomplete_df, self.model_cfg, self.train_cfg)

        with self.assertRaises(KeyError):
            model.predict(n_preds=3)

        # Create DataFrame without 'ID' column
        incomplete_df = self.sample_df.drop(columns=['ID'])
        model = ExponentialSmoothingModel(incomplete_df, self.model_cfg, self.train_cfg)

        with self.assertRaises(KeyError):
            model.predict(n_preds=3)

        # Create DataFrame without 'ds' column
        incomplete_df = self.sample_df.drop(columns=['ds'])
        model = ExponentialSmoothingModel(incomplete_df, self.model_cfg, self.train_cfg)

        with self.assertRaises(KeyError):
            model.predict(n_preds=3)

    def test_duplicate_dates_same_id(self):
        """Test with duplicate dates for the same ID"""
        # Create DataFrame with duplicate dates for ID1
        duplicate_data = {
            'ds': [pd.Timestamp('2023-01-01'), pd.Timestamp('2023-01-01'),
                   pd.Timestamp('2023-01-02'), pd.Timestamp('2023-01-03')] * 2,
            'y': [10, 11, 12, 13] * 2,
            'ID': ['ID1', 'ID1', 'ID1', 'ID1'] + ['ID2', 'ID2', 'ID2', 'ID2']
        }
        duplicate_df = pd.DataFrame(duplicate_data)
        model = ExponentialSmoothingModel(duplicate_df, self.model_cfg, self.train_cfg)

        # This should handle duplicates appropriately or raise an error
        with self.assertRaises(ValueError):
            model.predict(n_preds=23)


if __name__ == '__main__':
    unittest.main()
