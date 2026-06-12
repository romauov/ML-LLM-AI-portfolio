import unittest
import pandas as pd

from app.models.neuralprophet_model import NeuralprophetModel


class MockNPModelConfig:
    """Mock class for neuralprophet model configuration"""

    def __init__(self, yearly_seasonality=True, n_lags=5, n_changepoints=5,
                 changepoints_range=0.8, trend_reg=0.01, trend_local_reg=False,
                 seasonality_mode="additive", seasonality_reg=0.01,
                 seasonality_local_reg=False, ar_reg=0.01, normalize='auto',
                 learning_rate=0.01, n_forecasts=1):
        self.yearly_seasonality = yearly_seasonality
        self.n_lags = n_lags
        self.n_changepoints = n_changepoints
        self.changepoints_range = changepoints_range
        self.trend_reg = trend_reg
        self.trend_local_reg = trend_local_reg
        self.seasonality_mode = seasonality_mode
        self.seasonality_reg = seasonality_reg
        self.seasonality_local_reg = seasonality_local_reg
        self.ar_reg = ar_reg
        self.normalize = normalize
        self.learning_rate = learning_rate
        self.n_forecasts = n_forecasts

    def __iter__(self):
        # This allows converting to dict as expected by the model
        return iter([
            ('yearly_seasonality', self.yearly_seasonality),
            ('n_lags', self.n_lags),
            ('n_changepoints', self.n_changepoints),
            ('changepoints_range', self.changepoints_range),
            ('trend_reg', self.trend_reg),
            ('trend_local_reg', self.trend_local_reg),
            ('seasonality_mode', self.seasonality_mode),
            ('seasonality_reg', self.seasonality_reg),
            ('seasonality_local_reg', self.seasonality_local_reg),
            ('ar_reg', self.ar_reg),
            ('normalize', self.normalize),
            ('learning_rate', self.learning_rate),
            ('n_forecasts', self.n_forecasts)
        ])


class MockNPTrainConfig:
    """Mock class for neuralprophet train configuration"""

    def __init__(self, ew_lag=0, freq="D", n_epochs=5):
        self.ew_lag = ew_lag
        self.freq = freq
        self.n_epochs = n_epochs


class TestNeuralProphetModel(unittest.TestCase):

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
        self.model_cfg = MockNPModelConfig()
        self.train_cfg = MockNPTrainConfig()

    def test_initialization_with_valid_data(self):
        """Test initialization of NeuralprophetModel with valid data"""
        model = NeuralprophetModel(self.sample_df, self.model_cfg, self.train_cfg)

        self.assertIsInstance(model, NeuralprophetModel)
        # Note: The model removes constant columns, so we compare the shape after processing
        self.assertEqual(model.model_cfg, self.model_cfg)
        self.assertEqual(model.train_cfg, self.train_cfg)

    def test_predict_returns_correct_structure(self):
        """Test that predict method returns DataFrame with correct structure"""
        model = NeuralprophetModel(self.sample_df, self.model_cfg, self.train_cfg)
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
        model = NeuralprophetModel(self.sample_df, self.model_cfg, self.train_cfg)

        # Test with horizon of 1
        result_1 = model.predict(n_preds=1)
        self.assertEqual(len(result_1), 2)  # 1 prediction for each of 2 IDs

        # Test with horizon of 5
        result_5 = model.predict(n_preds=5)
        self.assertEqual(len(result_5), 10)  # 5 predictions for each of 2 IDs

    def test_predict_with_macroeconomic_indicators(self):
        """Test predict method with macroeconomic indicators"""
        # Add a macroeconomic column to the sample data
        dates = pd.date_range(start='2023-01-01', periods=10, freq='D')
        data = {
            'ds': dates.tolist() * 2,
            'y': [10, 12, 13, 14, 15, 16, 17, 18, 19, 20] * 2,
            'macro_econ': [1.0, 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7, 1.8, 1.9] * 2,
            'ID': ['ID1'] * 10 + ['ID2'] * 10
        }
        df_with_macro = pd.DataFrame(data)

        model = NeuralprophetModel(df_with_macro, self.model_cfg, self.train_cfg)
        result = model.predict(n_preds=2)

        # Check structure
        expected_columns = {'ds', 'pred', 'ID'}
        actual_columns = set(result.columns)
        self.assertEqual(expected_columns, actual_columns)

        # Check that both IDs are present
        expected_ids = set(df_with_macro['ID'].unique())
        actual_ids = set(result['ID'].unique())
        self.assertEqual(expected_ids, actual_ids)

    def test_predict_with_exponential_weighting(self):
        """Test predict method with exponential weighting"""
        model = NeuralprophetModel(self.sample_df, self.model_cfg, MockNPTrainConfig(ew_lag=2))
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
        """Test with single time series (one unique ID) - expected to raise error due to implementation limitation"""
        single_id_df = self.sample_df[self.sample_df['ID'] == 'ID1']
        model = NeuralprophetModel(single_id_df, self.model_cfg, self.train_cfg)

        result = model.predict(n_preds=3)

        # Check structure
        expected_columns = {'ds', 'pred', 'ID'}
        actual_columns = set(result.columns)
        self.assertEqual(expected_columns, actual_columns)

        # Check that ID are present
        expected_id = single_id_df['ID'].unique()
        actual_id = result['ID'].unique()
        self.assertEqual(expected_id, actual_id)

    def test_empty_dataframe_error_handling(self):
        """Test error handling with empty DataFrame"""
        empty_df = pd.DataFrame(columns=['ds', 'y', 'ID'])
        model = NeuralprophetModel(empty_df, self.model_cfg, self.train_cfg)

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
        model = NeuralprophetModel(minimal_df, self.model_cfg, self.train_cfg)

        with self.assertRaises(ValueError):
            model.predict(n_preds=3)

    def test_negative_prediction_horizon(self):
        """Test predict method with negative n_preds value"""
        model = NeuralprophetModel(self.sample_df, self.model_cfg, self.train_cfg)

        with self.assertRaises(ValueError):
            model.predict(n_preds=-1)

    def test_missing_required_columns(self):
        """Test predict method with missing required columns"""
        # Create DataFrame without 'y' column
        incomplete_df = self.sample_df.drop(columns=['y'])
        model = NeuralprophetModel(incomplete_df, self.model_cfg, self.train_cfg)

        with self.assertRaises(ValueError):
            model.predict(n_preds=3)

        # Create DataFrame without 'ID' column
        incomplete_df = self.sample_df.drop(columns=['ID'])
        model = NeuralprophetModel(incomplete_df, self.model_cfg, self.train_cfg)

        with self.assertRaises(ValueError):
            model.predict(n_preds=3)

        # Create DataFrame without 'ds' column
        incomplete_df = self.sample_df.drop(columns=['ds'])
        model = NeuralprophetModel(incomplete_df, self.model_cfg, self.train_cfg)

        with self.assertRaises(ValueError):
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
        model = NeuralprophetModel(duplicate_df, self.model_cfg, self.train_cfg)

        # This should handle duplicates appropriately or raise an error
        with self.assertRaises(ValueError):
            model.predict(n_preds=2)


if __name__ == '__main__':
    unittest.main()
