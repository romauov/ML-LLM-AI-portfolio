from types import SimpleNamespace

import pandas as pd

from app.predictor import predictor


def _make_cfg(use_only_light_models: bool):
    return SimpleNamespace(
        years_of_historical_data=3,
        use_only_light_models=use_only_light_models
    )


def _mock_df():
    return pd.DataFrame(
        [
            {'ds': '2025-01-01', 'y': 10.0, 'ID': 'series-1'},
            {'ds': '2025-01-08', 'y': 11.0, 'ID': 'series-1'},
        ]
    )


def test_predict_pipeline_adds_timesfm_task_for_full_mode(monkeypatch):
    calls = {'timesfm': 0, 'neuralprophet': 0}

    monkeypatch.setattr(predictor, 'get_data_from_database', lambda **_: _mock_df())
    monkeypatch.setattr(predictor, 'add_global_indicators', lambda df, cfg: df)
    monkeypatch.setattr(predictor, 'Dependency', lambda jobs: jobs)
    monkeypatch.setattr(predictor, 'set_predict_es_task', lambda *args: 'es')
    monkeypatch.setattr(predictor, 'set_predict_prophet_task', lambda *args: 'prophet')
    monkeypatch.setattr(predictor, 'set_predict_theta_task', lambda *args: 'theta')
    monkeypatch.setattr(predictor, 'set_save_result_task', lambda *args, **kwargs: None)
    monkeypatch.setattr(
        predictor,
        'set_predict_timesfm_task',
        lambda *args: calls.__setitem__('timesfm', calls['timesfm'] + 1) or 'timesfm'
    )
    monkeypatch.setattr(
        predictor,
        'set_predict_neuralprophet_task',
        lambda *args: calls.__setitem__('neuralprophet', calls['neuralprophet'] + 1) or 'neuralprophet'
    )

    predictor.predict_pipline(_make_cfg(use_only_light_models=False))

    assert calls['timesfm'] == 1
    assert calls['neuralprophet'] == 1


def test_predict_pipeline_skips_timesfm_for_light_mode(monkeypatch):
    calls = {'timesfm': 0, 'neuralprophet': 0}

    monkeypatch.setattr(predictor, 'get_data_from_database', lambda **_: _mock_df())
    monkeypatch.setattr(predictor, 'add_global_indicators', lambda df, cfg: df)
    monkeypatch.setattr(predictor, 'Dependency', lambda jobs: jobs)
    monkeypatch.setattr(predictor, 'set_predict_es_task', lambda *args: 'es')
    monkeypatch.setattr(predictor, 'set_predict_prophet_task', lambda *args: 'prophet')
    monkeypatch.setattr(predictor, 'set_predict_theta_task', lambda *args: 'theta')
    monkeypatch.setattr(predictor, 'set_save_result_task', lambda *args, **kwargs: None)
    monkeypatch.setattr(
        predictor,
        'set_predict_timesfm_task',
        lambda *args: calls.__setitem__('timesfm', calls['timesfm'] + 1) or 'timesfm'
    )
    monkeypatch.setattr(
        predictor,
        'set_predict_neuralprophet_task',
        lambda *args: calls.__setitem__('neuralprophet', calls['neuralprophet'] + 1) or 'neuralprophet'
    )

    predictor.predict_pipline(_make_cfg(use_only_light_models=True))

    assert calls['timesfm'] == 0
    assert calls['neuralprophet'] == 0
