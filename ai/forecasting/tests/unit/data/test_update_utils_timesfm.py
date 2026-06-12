from app.common.enums import DateFrequency
from config.update_utils import prepare_prediction_config


def test_prepare_prediction_config_updates_timesfm_settings():
    cfg = prepare_prediction_config(
        data_frequency=DateFrequency.MS,
        use_only_light_models=False,
        forecasting_steps=6,
        train_n_epochs=10,
        sesoanal_period=12
    )

    assert cfg.timesfm.train.freq == DateFrequency.MS
    assert cfg.timesfm.train.period == 12


def test_prepare_prediction_config_keeps_timesfm_model_defaults():
    cfg = prepare_prediction_config(
        data_frequency=DateFrequency.W_MON,
        use_only_light_models=True,
        forecasting_steps=8,
        train_n_epochs=None,
        sesoanal_period=52
    )

    assert cfg.timesfm.model.model_name == 'google/timesfm-2.5-200m-pytorch'
    assert cfg.timesfm.model.max_context > 0
