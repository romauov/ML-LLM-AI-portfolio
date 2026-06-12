import unittest
from unittest.mock import patch, MagicMock
import pandas as pd
import numpy as np

from app.data.checker import DataChecker
from tests.configs import get_test_config


class TestDataChecker(unittest.TestCase):

    def setUp(self):
        # Create a minimal config for testing with all required fields
        self.config = get_test_config()
        self.data_checker = DataChecker(self.config)

    @patch('pandas.read_excel')
    def test_excel_has_sheet_success(self, mock_read_excel):
        """Test that excel_has_sheet correctly identifies existing sheet"""
        # Mock the ExcelFile and read_excel
        with patch('pandas.ExcelFile', autospec=True) as mock_excel_file:
            mock_instance = MagicMock()
            mock_instance.sheet_names = ['Sheet1', 'Sheet2']
            mock_excel_file.return_value = mock_instance

            # Also mock read_excel to return a dummy DataFrame
            mock_read_excel.return_value = pd.DataFrame({'A': [1, 2, 3]})

            # This should not raise an exception and return a DataFrame
            result = self.data_checker.excel_has_sheet('dummy_path', 'Sheet1')

            # Verify that the function returns a DataFrame (not just True)
            self.assertIsInstance(result, pd.DataFrame)

    @patch('pandas.read_excel')
    def test_excel_has_sheet_failure(self, mock_read_excel):
        """Test that excel_has_sheet raises exception for non-existing sheet"""
        # Mock the ExcelFile and read_excel
        with patch('pandas.ExcelFile', autospec=True) as mock_excel_file:
            mock_instance = MagicMock()
            mock_instance.sheet_names = ['Sheet1', 'Sheet2']
            mock_excel_file.return_value = mock_instance

            # Also mock read_excel to return a dummy DataFrame
            mock_read_excel.return_value = pd.DataFrame({'A': [1, 2, 3]})

            with self.assertRaises(AssertionError):
                self.data_checker.excel_has_sheet('dummy_path', 'NonExistingSheet')

    def test_check_data_from_excel_valid_data(self):
        """Test checking valid Excel data"""
        # Create sample data with sufficient length for 3 seasons, limiting the date range to avoid filtering issues
        df = pd.DataFrame({
            'date': pd.date_range(start='2020-01-01', periods=200, freq='W-MON'),  # More than 3 seasons for weekly data
            'series': np.random.rand(200)
        })

        with patch('pandas.read_excel', return_value=df, autospec=True), \
                patch.object(self.data_checker, 'excel_has_sheet', return_value=df, autospec=True):
            # This should not raise any exceptions (using no history limit to avoid filtering issues)
            self.data_checker.check_data_from_excel(
                file_path='dummy_path',
                sheet_name='Sheet1',
                date_name='date',
                series_name='series',
                history_years_limit=None  # Use None to avoid filtering
            )

    def test_check_data_from_excel_invalid_data(self):
        """Test checking invalid Excel data raises appropriate errors"""
        # Create sample data with insufficient points
        df = pd.DataFrame({
            'date': pd.date_range(start='2023-01-01', periods=1, freq='W-MON'),
            'series': [1.0]
        })

        with patch('pandas.read_excel', return_value=df, autospec=True), \
                patch.object(self.data_checker, 'excel_has_sheet', return_value=df, autospec=True):
            # This should raise an HTTPException due to insufficient data points (because of the decorator)
            with self.assertRaises(Exception):  # Using generic Exception to catch HTTPException
                self.data_checker.check_data_from_excel(
                    file_path='dummy_path',
                    sheet_name='Sheet1',
                    date_name='date',
                    series_name='series',
                    history_years_limit=5
                )

    def test_check_data_from_excel_wrong_date_format(self):
        """Test checking Excel data with wrong date format raises appropriate errors"""
        # Create sample data with string dates that can't be parsed
        df = pd.DataFrame({
            'date': ['not_a_date', 'also_not_a_date', 'still_not_a_date'],
            'series': [1.0, 2.0, 3.0]
        })

        with patch('pandas.read_excel', return_value=df, autospec=True), \
                patch.object(self.data_checker, 'excel_has_sheet', return_value=df, autospec=True):
            # This should raise an ValueError due to wrong date format
            with self.assertRaises(ValueError):
                self.data_checker.check_data_from_excel(
                    file_path='dummy_path',
                    sheet_name='Sheet1',
                    date_name='date',
                    series_name='series',
                    history_years_limit=5
                )

    def test_check_data_from_excel_missing_columns(self):
        """Test checking Excel data with missing required columns raises appropriate errors"""
        # Create sample data without required columns
        df = pd.DataFrame({
            'wrong_column_name': pd.date_range(start='2020-01-01', periods=160, freq='W-MON'),
            'another_wrong_name': np.random.rand(160)
        })

        with patch('pandas.read_excel', return_value=df, autospec=True), \
                patch.object(self.data_checker, 'excel_has_sheet', return_value=df):
            # This should raise an HTTPException due to missing required columns (because of the decorator)
            with self.assertRaises(Exception):  # Using generic Exception to catch HTTPException
                self.data_checker.check_data_from_excel(
                    file_path='dummy_path',
                    sheet_name='Sheet1',
                    date_name='date',
                    series_name='series',
                    history_years_limit=5
                )

    def test_check_data_from_excel_with_nan_values(self):
        """Test checking Excel data with NaN values raises appropriate errors"""
        # Create sample data with NaN values
        df = pd.DataFrame({
            'date': pd.date_range(start='2020-01-01', periods=160, freq='W-MON'),
            'series': [1.0, 2.0, np.nan, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0] + [i for i in range(11, 161)]
        })

        with patch('pandas.read_excel', return_value=df, autospec=True), \
                patch.object(self.data_checker, 'excel_has_sheet', return_value=df):

            with self.assertRaises(Exception):
                self.data_checker.check_data_from_excel(
                    file_path='dummy_path',
                    sheet_name='Sheet1',
                    date_name='date',
                    series_name='series',
                    history_years_limit=5
                )

    def test_check_data_from_database_valid_data(self):
        """Test checking valid database data"""
        # Create sample data with enough points for 3 seasons (for weekly data, we need at least 3*52 = 156 points)
        df = pd.DataFrame({
            'ds': pd.date_range(start='2020-01-01', periods=160, freq='W-MON'),  # More than 3 seasons for weekly data
            'y': np.random.rand(160),
            'ID': ['test_id'] * 160
        })

        # This should not raise any exceptions
        self.data_checker.check_data_from_database(df, 'ID')

    def test_check_data_from_database_invalid_data(self):
        """Test checking invalid database data raises appropriate errors"""
        # Create sample data with insufficient unique points
        df = pd.DataFrame({
            'ds': pd.date_range(start='2023-01-01', periods=1, freq='W-MON'),
            'y': [1.0],
            'ID': ['test_id']
        })

        # This should raise a ValueError due to insufficient dates to infer frequency
        with self.assertRaises(ValueError):
            self.data_checker.check_data_from_database(df, 'ID')

    def test_check_data_from_database_duplicate_dates(self):
        """Test checking data with duplicate dates raises appropriate errors"""
        # Create sample data with duplicate dates
        df = pd.DataFrame({
            'ds': pd.to_datetime(['2023-01-01', '2023-01-01', '2023-01-08']),
            'y': [1.0, 1.1, 2.0],
            'ID': ['test_id'] * 3
        })

        # This should raise an AssertionError when trying to infer frequency from duplicate dates
        with self.assertRaises(AssertionError):
            self.data_checker.check_data_from_database(df, 'ID')

    def test_check_data_from_database_wrong_date_format(self):
        """Test checking database data with wrong date format raises appropriate errors"""
        # Create sample data with string dates that can't be parsed as datetime
        df = pd.DataFrame({
            'ds': ['not_a_date', 'also_not_a_date', 'still_not_a_date'],
            'y': [1.0, 2.0, 3.0],
            'ID': ['test_id'] * 3
        })

        # This should raise an ValueError due to wrong date format
        with self.assertRaises(ValueError):
            self.data_checker.check_data_from_database(df, 'ID')

    def test_check_data_from_database_missing_columns(self):
        """Test checking database data with missing required columns raises appropriate errors"""
        # Create sample data without required columns
        df = pd.DataFrame({
            'wrong_ds_column': pd.date_range(start='2020-01-01', periods=160, freq='W-MON'),
            'wrong_y_column': np.random.rand(160),
            'ID': ['test_id'] * 160
        })

        # This should raise an KeyError due to missing required columns
        with self.assertRaises(KeyError):
            self.data_checker.check_data_from_database(df, 'ID')

    def test_check_data_from_database_with_nan_values(self):
        """Test checking database data with NaN values does not raise errors (function doesn't check for NaN)"""
        # Create sample data with NaN values
        df = pd.DataFrame({
            'ds': pd.date_range(start='2020-01-01', periods=160, freq='W-MON'),
            'y': [1.0, 2.0, np.nan, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0] + [i for i in range(11, 161)],
            'ID': ['test_id'] * 160
        })

        # The function doesn't explicitly check for NaN values, so this should not raise an exception
        self.data_checker.check_data_from_database(df, 'ID')

    def test_check_data_from_database_empty_dataframe(self):
        """Test checking empty database data raises appropriate errors"""
        # Create empty DataFrame
        df = pd.DataFrame({
            'ds': pd.Series([], dtype='datetime64[ns]'),
            'y': pd.Series([], dtype='float64'),
            'ID': pd.Series([], dtype='object')
        })

        # This should raise an IndexError when trying to access the first element of an empty series
        with self.assertRaises(IndexError):
            self.data_checker.check_data_from_database(df, 'ID')


class TestDataCheckerStaticMethods(unittest.TestCase):

    def test_df_has_col_success(self):
        """Test that df_has_col succeeds when column exists"""
        df = pd.DataFrame({
            'existing_col': [1, 2, 3],
            'another_col': ['a', 'b', 'c']
        })

        # This should not raise an exception
        DataChecker.df_has_col(df, 'existing_col')

    def test_df_has_col_failure(self):
        """Test that df_has_col raises AssertionError when column does not exist"""
        df = pd.DataFrame({
            'existing_col': [1, 2, 3],
            'another_col': ['a', 'b', 'c']
        })

        with self.assertRaises(AssertionError):
            DataChecker.df_has_col(df, 'non_existing_col')

    def test_df_date_frequency_success(self):
        """Test that df_date_frequency succeeds with regular frequency"""
        df = pd.DataFrame({
            'date_col': pd.date_range(start='2023-01-01', periods=10, freq='D'),
            'value': range(10)
        })

        freq = DataChecker.df_date_frequency(df, 'date_col')
        self.assertIn(freq, ['D', '1D'])  # Different pandas versions may return slightly different formats

    def test_df_date_frequency_irregular(self):
        """Test that df_date_frequency raises AssertionError with irregular dates"""
        df = pd.DataFrame({
            'date_col': pd.to_datetime(['2023-01-01', '2023-01-03', '2023-01-06']),  # Irregular intervals
            'value': [1, 2, 3]
        })

        with self.assertRaises(AssertionError):
            DataChecker.df_date_frequency(df, 'date_col')

    def test_df_date_frequency_single_date(self):
        """Test that df_date_frequency raises ValueError with single date"""
        df = pd.DataFrame({
            'date_col': pd.to_datetime(['2023-01-01']),
            'value': [1]
        })

        with self.assertRaises(ValueError):
            DataChecker.df_date_frequency(df, 'date_col')

    def test_df_min_length_sufficient(self):
        """Test that df_min_length succeeds when data length is sufficient"""
        df = pd.DataFrame({
            'value': range(100)  # Sufficient length for any reasonable season_length * 3
        })

        # This should not raise an exception for small season lengths
        DataChecker.df_min_length(df, 10)  # 10 * 3 = 30, df has 100 rows

    def test_df_min_length_insufficient(self):
        """Test that df_min_length raises AssertionError when data length is insufficient"""
        df = pd.DataFrame({
            'value': range(20)  # Insufficient length: 20 < 30 (for season_length=10)
        })

        with self.assertRaises(AssertionError):
            DataChecker.df_min_length(df, 10)  # 10 * 3 = 30, but df has only 20 rows


if __name__ == '__main__':
    unittest.main()
