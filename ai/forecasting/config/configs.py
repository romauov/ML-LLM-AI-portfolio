import os
from typing import List, Optional, Union
from pydantic import BaseModel
from omegaconf import OmegaConf


class _Scheduler(BaseModel, extra='allow'):
    day_of_week: Optional[str] = None
    day: Optional[int | str] = None
    hour: int
    minute: int


class Scheduler(BaseModel, extra='allow'):
    forecasting: _Scheduler
    dashboards: _Scheduler


class _ExponentialSmoothingModel(BaseModel, extra='allow'):
    seasonal_periods: int
    trend: str
    seasonal: str
    damped_trend: bool
    use_boxcox: bool
    freq: str


class _ExponentialSmoothingTrain(BaseModel, extra='allow'):
    ew_lag: int


class ExponentialSmoothing(BaseModel, extra='allow'):
    model: _ExponentialSmoothingModel
    train: _ExponentialSmoothingTrain


class _NeuralprophetModel(BaseModel, extra='allow'):
    drop_missing: bool
    unknown_data_normalization: bool
    trend_global_local: str
    season_global_local: str
    yearly_seasonality: bool
    weekly_seasonality: bool
    daily_seasonality: bool
    learning_rate: float
    n_lags: int
    n_forecasts: int


class _NeuralprophetTrain(BaseModel, extra='allow'):
    ew_lag: int
    freq: str
    n_epochs: Optional[int] = None
    period: int


class Neuralprophet(BaseModel, extra='allow'):
    model: _NeuralprophetModel
    train: _NeuralprophetTrain


class _ProphetModel(BaseModel, extra='allow'):
    growth: str
    n_changepoints: int
    changepoint_range: float
    yearly_seasonality: Union[str, bool]
    weekly_seasonality: Union[str, bool]
    daily_seasonality: Union[str, bool]
    seasonality_mode: str
    seasonality_prior_scale: float
    holidays_prior_scale: float
    changepoint_prior_scale: float
    holidays_mode: str


class _ProphetTrain(BaseModel, extra='allow'):
    period: int
    ew_lag: int


class Prophet(BaseModel, extra='allow'):
    model: _ProphetModel
    train: _ProphetTrain


class _ThetaModel(BaseModel, extra='allow'):
    period: int


class _ThetaTrain(BaseModel, extra='allow'):
    ew_lag: int
    theta: int
    use_mle: bool
    freq: str


class Theta(BaseModel, extra='allow'):
    model: _ThetaModel
    train: _ThetaTrain


class _ArimaModel(BaseModel, extra='allow'):
    p: int
    d: int
    q: int
    P: int
    D: int
    Q: int
    s: int
    simple_differencing: bool
    fit_intercept: bool


class _ArimaTrain(BaseModel, extra='allow'):
    method: str
    freq: str


class Arima(BaseModel, extra='allow'):
    model: _ArimaModel
    train: _ArimaTrain


class _TimesfmModel(BaseModel, extra='allow'):
    model_name: str
    max_context: int
    normalize_inputs: bool
    use_continuous_quantile_head: bool
    infer_is_positive: bool


class _TimesfmTrain(BaseModel, extra='allow'):
    ew_lag: int
    freq: str
    period: int


class Timesfm(BaseModel, extra='allow'):
    model: _TimesfmModel
    train: _TimesfmTrain


class CommonSeaFoodProduct(BaseModel, extra='allow'):
    name: Optional[str] = None
    product_type: Optional[List[Optional[str]]] = None
    fish_type: Optional[List[Optional[str]]] = None
    cutting: Optional[List[Optional[str]]] = None
    cook_method: Optional[List[Optional[str]]] = None
    filling: Optional[List[Optional[str]]] = None
    goods_type: Optional[List[Optional[str]]] = None
    smoking: Optional[List[Optional[str]]] = None
    sort: Optional[List[Optional[str]]] = None
    size: Optional[List[Optional[str]]] = None
    temperature_state: Optional[List[Optional[str]]] = None
    salt: Optional[List[Optional[str]]] = None
    period: Optional[List[Optional[str]]] = None
    boxing: Optional[List[Optional[str]]] = None


class CommonMeatProduct(BaseModel, extra='allow'):
    product: Optional[List[Optional[str]]] = None
    product_type: Optional[List[Optional[str]]] = None
    sort: Optional[List[Optional[str]]] = None
    certification: Optional[List[Optional[str]]] = None
    temperature_state: Optional[List[Optional[str]]] = None
    product_details: Optional[List[Optional[str]]] = None


class Config(BaseModel, extra='allow'):
    scheduler: Scheduler
    exponential_smoothing: ExponentialSmoothing
    neuralprophet: Neuralprophet
    prophet: Prophet
    theta: Theta
    arima: Arima
    timesfm: Timesfm
    outliers_sliding_window_size: int
    meat_products: Optional[List[CommonMeatProduct]] = None
    n_forecasts: int
    optuna_n_trials: int
    cross_validation_k_folds: int
    min_unique_points: int
    freq: str
    years_of_historical_data: int
    use_only_light_models: bool
    macroeconomic_indicators: List[str]
    agro_indicators: List[str]
    agro_indicators_product_categories: List[str] = None
    seafood_products: Optional[List[CommonSeaFoodProduct]] = None
    caviar_products: Optional[List[CommonSeaFoodProduct]] = None
    fish_products: Optional[List[CommonSeaFoodProduct]] = None
    shrimp_products: Optional[List[CommonSeaFoodProduct]] = None
    semiprocessed_products: Optional[List[CommonSeaFoodProduct]] = None

    @classmethod
    def from_yaml_week(cls) -> 'Config':
        path = 'storage/config.yaml' if os.path.exists('storage/config.yaml') else 'config/config.yaml'
        cfg = OmegaConf.to_container(OmegaConf.load(path), resolve=True)
        return cls(**cfg)

    @classmethod
    def from_yaml_month(cls) -> 'Config':
        path = 'storage/month_config.yaml' if os.path.exists(
            'storage/month_config.yaml') else 'config/month_config.yaml'
        cfg = OmegaConf.to_container(OmegaConf.load(path), resolve=True)
        return cls(**cfg)
