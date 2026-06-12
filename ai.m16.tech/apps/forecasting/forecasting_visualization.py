"""
Метрики для оценки модели, построение диаграмм

@author Dmitry Abramov
"""
import io
from PIL import Image

import pandas as pd
import matplotlib.pyplot as plt


# pylint: disable=too-many-arguments
def validation_plot(actual, predicted, index1, y_col, steps, _mape, _mae, path):
    """
    Построение диаграммы для валидации модели

    actual: np.array - реальные данные
    predicted: np.array - спрогнозированные данные
    index1: list(pd.datetime) - индексы - даты
    y_col: str - колонка для прогнозирования
    steps: int - количество шагов прогнозирования
    mape: float - MAPE на валидации
    mae: float - МАE на валидации
    path: str - путь директории результатов
    """
    val_df = pd.DataFrame({'Реальная цена': actual,
                           'Прогноз': predicted,
                           'date': index1})

    val_df.date = pd.to_datetime(val_df.date)

    val_df.set_index('date').plot()
    plt.title(f'Проверочное прогнозирование {y_col} на {steps} шагов.\nMAPE: {_mape:.2f}% MAE: {_mae:.2f}')
    plt.legend()

    if path:
        plt.savefig(path + '/validation_plot.png', format='png', bbox_inches='tight')

    img_buf = io.BytesIO()
    plt.savefig(img_buf, format='png', bbox_inches='tight')

    return Image.open(img_buf)


def forecasting_plot(forecast, y_col, steps, path):
    """
    Построение диаграммы прогноза

    forecast: pd.DataFrame - датафрейм-прогноз
        schema: 
            [('Дата', pd.datetime64),
            ('Прогноз': float)]
    y_col: str - колонка для прогнозирования
    steps: int - количество шагов прогнозирования
    path: str - путь директории результатов
    """
    forecast.set_index('Дата').plot()
    plt.title(f'Прогнозирование {y_col} на {steps} шагов')

    if path:
        plt.savefig(path + '/forecast_plot.png', format='png', bbox_inches='tight')

    img_buf = io.BytesIO()
    plt.savefig(img_buf, format='png', bbox_inches='tight')
    return Image.open(img_buf)


def forecasting_plot_bins(forecast, path):
    """
    Визуализация прогноза

    forecast: pd.DataFrame - датафрейм-прогноз
        schema: 
            [('Дата', pd.datetime64),
            ('Прогноз': float)]
    path: str - путь директории результатов
    """
    forecasting = forecast.copy()
    color = 'tab:blue'

    _, ax1 = plt.subplots(figsize=(16, 9))

    for date, value in forecasting.reset_index()[['index', 'Прогноз']].values:
        ax1.text(date, value + value // 150, str(round(value, 1)), ha='center')

    forecasting.Прогноз.plot(kind='bar',
                           color=color,
                           ax=ax1)

    ax2 = ax1.twinx()

    color = 'tab:red'

    forecasting['percente_diff'] = forecasting['Прогноз'].diff() / forecasting['Прогноз'] * 100

    forecasting['percente_diff'].plot(kind='line',
                                      color=color,
                                      marker='o',
                                      ax=ax2)

    for date, value, diff in forecasting.reset_index()[['index', 'Прогноз', 'percente_diff']].values[1:]:
        ax2.text(date, diff + 1, f"{round(diff, 1)}%",
                 ha='center',
                 bbox={'facecolor': 'white',
                       'edgecolor': 'white',
                       'pad': 3.0}
                 )

    ax2.axis('off')
    ax2.set_ylim(forecasting.percente_diff.min() - 5, forecasting.percente_diff.max() * 4)

    ax1.set_xticks(list(range(len(forecasting.Дата.dt.date.values))),
                   forecasting.Дата.dt.date.values)
    if path:
        plt.savefig(path + '/bins_plot.png',
                    format='png',
                    bbox_inches='tight')

    img_buf = io.BytesIO()

    plt.savefig(img_buf, format='png', bbox_inches='tight')
    return Image.open(img_buf)
