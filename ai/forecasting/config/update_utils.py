from typing import TypeVar

from config.configs import Config

DateFrequencyT = TypeVar('DateFrequencyT', bound='DateFrequency')


def prepare_prediction_config(
        data_frequency: DateFrequencyT,
        use_only_light_models: bool,
        forecasting_steps: int,
        train_n_epochs: int | None,
        sesoanal_period: int
) -> Config:
    """
    Подготовка конфигурации для пайплайна предсказания.

    :param data_frequency: Частотность данных.
    :param use_only_light_models: Флаг использования только легких моделей. Исключается NeuralProphet.
    :param forecasting_steps: Количество шагов для предсказания.
    :param train_n_epochs: Количество эпох обучения neuralprophet.
    :param sesoanal_period: Длина сезонного периода.
    :return: Настроенный объект конфигурации.
    """
    cfg = Config.from_yaml_week()

    # общие параметры
    cfg.freq = data_frequency
    cfg.use_only_light_models = use_only_light_models
    cfg.n_forecasts = forecasting_steps

    # обновление специфичных параметров моделей
    _update_neuralprophet_config(cfg, data_frequency, train_n_epochs)
    _update_exponential_smoothing_config(cfg, data_frequency, sesoanal_period)
    _update_prophet_config(cfg, data_frequency)
    _update_theta_config(cfg, data_frequency, sesoanal_period)
    _update_arima_config(cfg, data_frequency, sesoanal_period)
    _update_timesfm_config(cfg, data_frequency, sesoanal_period)

    return cfg


def _update_neuralprophet_config(
        cfg: Config,
        data_frequency: DateFrequencyT,
        train_n_epochs: int | None
) -> None:
    cfg.neuralprophet.train.freq = data_frequency
    cfg.neuralprophet.train.n_epochs = train_n_epochs


def _update_exponential_smoothing_config(
        cfg: Config,
        data_frequency: DateFrequencyT,
        seasonal_periods: int
) -> None:
    cfg.exponential_smoothing.model.freq = data_frequency
    cfg.exponential_smoothing.model.seasonal_periods = seasonal_periods


def _update_prophet_config(
        cfg: Config,
        data_frequency: DateFrequencyT
) -> None:
    cfg.prophet.train.freq = data_frequency


def _update_theta_config(
        cfg: Config,
        data_frequency: DateFrequencyT,
        period: int
) -> None:
    cfg.theta.model.period = period
    cfg.theta.train.freq = data_frequency


def _update_arima_config(
        cfg: Config,
        data_frequency: DateFrequencyT,
        s: int
) -> None:
    cfg.arima.train.freq = data_frequency
    cfg.arima.model.s = s


def _update_timesfm_config(
        cfg: Config,
        data_frequency: DateFrequencyT,
        period: int
) -> None:
    cfg.timesfm.train.freq = data_frequency
    cfg.timesfm.train.period = period
