import unittest
import pandas as pd

from app.models.prophet_model import ProphetModel


class MockProphetModelConfig:
    """Mock class for prophet model configuration"""

    def __init__(self, growth='linear', n_changepoints=25, changepoint_range=0.8,
                 yearly_seasonality=True, weekly_seasonality='auto', daily_seasonality='auto',
                 seasonality_mode='additive', seasonality_prior_scale=10.0,
                 holidays_prior_scale=10.0, changepoint_prior_scale=0.05,
                 holidays_mode='additive', freq="D"):
        self.growth = growth
        self.n_changepoints = n_changepoints
        self.changepoint_range = changepoint_range
        self.yearly_seasonality = yearly_seasonality
        self.weekly_seasonality = weekly_seasonality
        self.daily_seasonality = daily_seasonality
        self.seasonality_mode = seasonality_mode
        self.seasonality_prior_scale = seasonality_prior_scale
        self.holidays_prior_scale = holidays_prior_scale
        self.changepoint_prior_scale = changepoint_prior_scale
        self.holidays_mode = holidays_mode
        self.freq = freq

    def __iter__(self):
        # This allows converting to dict as expected by the model
        return iter([
            ('growth', self.growth),
            ('n_changepoints', self.n_changepoints),
            ('changepoint_range', self.changepoint_range),
            ('yearly_seasonality', self.yearly_seasonality),
            ('weekly_seasonality', self.weekly_seasonality),
            ('daily_seasonality', self.daily_seasonality),
            ('seasonality_mode', self.seasonality_mode),
            ('seasonality_prior_scale', self.seasonality_prior_scale),
            ('holidays_prior_scale', self.holidays_prior_scale),
            ('changepoint_prior_scale', self.changepoint_prior_scale),
            ('holidays_mode', self.holidays_mode)
        ])


class MockProphetTrainConfig:
    """Mock class for prophet train configuration"""

    def __init__(self, ew_lag=0, freq="D"):
        self.ew_lag = ew_lag
        self.freq = freq


class TestProphetModel(unittest.TestCase):

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
        self.model_cfg = MockProphetModelConfig()
        self.train_cfg = MockProphetTrainConfig()

    def test_initialization_with_valid_data(self):
        """Test initialization of ProphetModel with valid data"""
        model = ProphetModel(self.sample_df, self.model_cfg, self.train_cfg)

        self.assertIsInstance(model, ProphetModel)
        pd.testing.assert_frame_equal(model.df, self.sample_df)
        self.assertEqual(model.model_cfg, self.model_cfg)
        self.assertEqual(model.train_cfg, self.train_cfg)

    def test_predict_returns_correct_structure(self):
        """Test that predict method returns DataFrame with correct structure"""
        model = ProphetModel(self.sample_df, self.model_cfg, self.train_cfg)
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
        model = ProphetModel(self.sample_df, self.model_cfg, self.train_cfg)

        # Test with horizon of 1
        result_1 = model.predict(n_preds=1)
        self.assertEqual(len(result_1), 2)  # 1 prediction for each of 2 IDs

        # Test with horizon of 5
        result_5 = model.predict(n_preds=5)
        self.assertEqual(len(result_5), 10)  # 5 predictions for each of 2 IDs

    def test_predict_without_exponential_weighting(self):
        """Test predict method with ew_lag = 0 (no exponential weighting)"""
        model = ProphetModel(self.sample_df, self.model_cfg, MockProphetTrainConfig(ew_lag=0))
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
        model = ProphetModel(self.sample_df, self.model_cfg, MockProphetTrainConfig(ew_lag=2))
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
        model = ProphetModel(single_id_df, self.model_cfg, self.train_cfg)
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
        model = ProphetModel(empty_df, self.model_cfg, self.train_cfg)

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
        model = ProphetModel(minimal_df, self.model_cfg, self.train_cfg)

        with self.assertRaises(Exception):
            model.predict(n_preds=3)

    def test_negative_prediction_horizon(self):
        """Test predict method with negative n_preds value"""
        model = ProphetModel(self.sample_df, self.model_cfg, self.train_cfg)

        # ProphetModel handles negative n_preds without raising an exception
        # It might return unexpected results, so we test the structure
        result = model.predict(n_preds=-1)

        # Check that result is a DataFrame
        self.assertIsInstance(result, pd.DataFrame)

        # Check that result has the expected columns
        expected_columns = {'ds', 'pred', 'ID'}
        actual_columns = set(result.columns)
        self.assertEqual(expected_columns, actual_columns)

    def test_missing_required_columns(self):
        """Test predict method with missing required columns"""
        # Create DataFrame without 'y' column
        incomplete_df = self.sample_df.drop(columns=['y'])
        model = ProphetModel(incomplete_df, self.model_cfg, self.train_cfg)

        with self.assertRaises(KeyError):
            model.predict(n_preds=3)

        # Create DataFrame without 'ID' column
        incomplete_df = self.sample_df.drop(columns=['ID'])
        model = ProphetModel(incomplete_df, self.model_cfg, self.train_cfg)

        with self.assertRaises(KeyError):
            model.predict(n_preds=3)

        # Create DataFrame without 'ds' column
        incomplete_df = self.sample_df.drop(columns=['ds'])
        model = ProphetModel(incomplete_df, self.model_cfg, self.train_cfg)

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
        model = ProphetModel(duplicate_df, self.model_cfg, self.train_cfg)

        # ProphetModel handles duplicate dates without raising an exception
        result = model.predict(n_preds=3)

        # Check that result is a DataFrame
        self.assertIsInstance(result, pd.DataFrame)

        # Check that result has the expected columns
        expected_columns = {'ds', 'pred', 'ID'}
        actual_columns = set(result.columns)
        self.assertEqual(expected_columns, actual_columns)

        # Check that result contains expected IDs
        expected_ids = set(duplicate_df['ID'].unique())
        actual_ids = set(result['ID'].unique())
        self.assertEqual(expected_ids, actual_ids)


if __name__ == '__main__':
    unittest.main()
