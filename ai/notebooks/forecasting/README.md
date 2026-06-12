Тут собраны ноутбуки в которых проводилось исследование на предмет использования различных моделей для предсказания временных рядов.

Разведочный анализ данных [eda.ipynb](eda.ipynb)

Бустинги [classic_models_predictor.ipynb](classic_models_predictor.ipynb)

RNN [rnn_forecast.ipynb](rnn_forecast.ipynb)

Neuralprophet [prophet_predictor.ipynb](prophet_predictor.ipynb)

Итоговое решение: использовать две модели Neuralprophet и Экспоненциальное сглаживание (Exponential smoothing). 
Для каждого временного ряда откладывается валидационная выборка, далее строится прогноз обеими моделями и выбирается лучший результат по MAPE на валидационной выборке.
Затем лучшая модель делает предсказание уже на всей выборке.