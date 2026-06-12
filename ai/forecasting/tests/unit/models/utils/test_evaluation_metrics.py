import unittest
import numpy as np
from app.common.evaluation_metrics import mean_absolute_percentage_error


class TestEvaluationMetrics(unittest.TestCase):

    def test_mean_absolute_percentage_error_perfect_prediction(self):
        """Test MAPE with perfect predictions (should be 0)"""
        y_true = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        y_pred = np.array([1.0, 2.0, 3.0, 4.0, 5.0])

        mape = mean_absolute_percentage_error(y_true, y_pred)

        # Perfect predictions should yield 0 MAPE
        self.assertEqual(mape, 0.0)

    def test_mean_absolute_percentage_error_positive_values(self):
        """Test MAPE with positive values"""
        y_true = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        y_pred = np.array([1.0, 2.0, 3.0, 4.0, 6.0])

        mape = mean_absolute_percentage_error(y_true, y_pred)

        # MAPE should be positive and reasonably small
        self.assertEqual(mape, 4.0)

    def test_mean_absolute_percentage_error_edge_case_zeros_in_true(self):
        """Test MAPE behavior with zeros in true values (should raise error or handle appropriately)"""
        y_true = np.array([0.0, 2.0, 3.0])
        y_pred = np.array([1.0, 2.0, 3.0])

        # Division by zero will occur, causing infinity
        mape = mean_absolute_percentage_error(y_true, y_pred)

        # This will result in infinity due to division by zero
        self.assertTrue(np.isinf(mape))


if __name__ == '__main__':
    unittest.main()
