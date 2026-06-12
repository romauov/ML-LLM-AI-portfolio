import unittest

from app.models.exponential_smoothing_model import ExponentialSmoothingModel
from app.models.models_handler import ModelsHandler
from app.models.neuralprophet_model import NeuralprophetModel
from app.models.prophet_model import ProphetModel
from tests.configs import get_test_config


class TestModelsHandler(unittest.TestCase):

    def setUp(self):
        # Create a minimal config for testing
        self.config = get_test_config()

    def test_get_models_all_models_enabled(self):
        """Test getting all models when light models flag is False"""
        # Set config to use all models
        self.config.use_only_light_models = False

        handler = ModelsHandler(self.config)
        models = handler.get_models()

        # Should return 4 models: Exponential smoothing, NeuralProphet, Prophet, ThetaModel
        self.assertEqual(len(models), 4)

        # Check that all expected models are present
        model_cls = [model['model_cls'] for model in models]
        self.assertIn(ExponentialSmoothingModel, model_cls)
        self.assertIn(NeuralprophetModel, model_cls)
        self.assertIn(ProphetModel, model_cls)

    def test_get_models_light_models_only(self):
        """Test getting only light models when light models flag is True"""
        # Set config to use only light models
        self.config.use_only_light_models = True

        handler = ModelsHandler(self.config)
        models = handler.get_models()

        # Should return 3 models: Exponential smoothing, Prophet, ThethaModel, (no NeuralProphet)
        self.assertEqual(len(models), 3)

        # Check that only the expected models are present
        model_cls = [model['model_cls'] for model in models]
        self.assertIn(ExponentialSmoothingModel, model_cls)
        self.assertIn(ProphetModel, model_cls)
        self.assertNotIn(NeuralprophetModel, model_cls)

    def test_get_models_names_all_models_enabled(self):
        """Test getting all model names when light models flag is False"""
        # Set config to use all models
        self.config.use_only_light_models = False

        handler = ModelsHandler(self.config)
        model_names = handler.get_models_names()

        # Should return 4 model names: Exponential smoothing, NeuralProphet, Prophet, ThetaModel
        self.assertEqual(len(model_names), 4)

        # Check that all expected model names are present
        self.assertIn('Exponential smoothing', model_names)
        self.assertIn('NeuralProphet', model_names)
        self.assertIn('Prophet', model_names)

    def test_get_models_names_light_models_only(self):
        """Test getting only light model names when light models flag is True"""
        # Set config to use only light models
        self.config.use_only_light_models = True

        handler = ModelsHandler(self.config)
        model_names = handler.get_models_names()

        # Should return 3 model names: Exponential smoothing, Prophet, ThetaModel (no NeuralProphet)
        self.assertEqual(len(model_names), 3)

        # Check that only the expected model names are present
        self.assertIn('Exponential smoothing', model_names)
        self.assertIn('Prophet', model_names)
        self.assertNotIn('NeuralProphet', model_names)

    def test_model_structure(self):
        """Test that each model has the expected structure"""
        self.config.use_only_light_models = False
        handler = ModelsHandler(self.config)
        models = handler.get_models()

        for model in models:
            # Each model should have the required keys
            self.assertIn('name', model)
            self.assertIn('optuna_function', model)
            self.assertIn('model_cls', model)

            # Name should be a string
            self.assertIsInstance(model['name'], str)

            # optuna_function should be callable
            self.assertTrue(callable(model['optuna_function']))

            # model_cls should be a class/type
            self.assertTrue(hasattr(model['model_cls'], '__call__'))


if __name__ == '__main__':
    unittest.main()
