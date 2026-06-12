"""
Демостраница автоматического прогнозирования

@author Dmitry Abramov
"""
import gradio as gr

from .pipeline import pipeline, get_result
from .db_logging import db_rows
from .pipeline_gl import pipeline_glocal, get_result_gl


# pylint: disable=too-many-statements
def gr_forecasting_interface():
    """
    Демостраница автоматического прогнозирования
    """
    with gr.Blocks() as interface:
        with gr.Tabs():
            with gr.TabItem("Прогнозирование"):
                with gr.Row():
                    sheet_name = gr.Text(label='Название таблицы/листа в excel файле')
                    ds_col = gr.Text(label='Название столбца, в котором находится дата')
                    y_col = gr.Text(label='Столбец, который нужно спрогнозировать')
                    steps = gr.Number(value=12, precision=0,
                                      label='Количество шагов прогнозирования')
                    validations_steps = gr.Number(value=12, precision=0,
                                                  label='Количество шагов для валидации и настройки параметров')
                    trials = gr.Number(value=50, precision=0,
                                       label='Количество запусков настройки гиперпараметров')
                    n_ensemble = gr.Number(value=15, precision=0,
                                           label='Количество прогнозаторов в ансамбле')
                with gr.Row():
                    use_save = gr.Radio(['Нет', 'Да'], value='Да',
                                        label='Использовать сохраненные результаты')
                    date_border = gr.Text(label='Ограничение по дате')
                    years = gr.Number(value=10, precision=0,
                                      label='За сколько последних лет брать данные')

                with gr.Column():
                    temp_file = gr.File(file_types=['.csv', '.xlsx', '.xls'],
                                        label='Файл с данными')

                with gr.Row():
                    recommendation = gr.Button("Начать прогнозирование")

                with gr.Row():
                    run_id = gr.Number(label='id запуска', precision=0)
                    path = gr.Text(label='директория экспериментов')

                with gr.Row():
                    file_output = gr.File(label='Файл с прогнозом')

                with gr.Column():
                    with gr.Row():
                        val_img = gr.Image(show_label="")
                        forecast_img = gr.Image(show_label="")
                    with gr.Row():
                        bins_img = gr.Image(show_label="")
                        model_forecast_img = gr.Image(label='Прогноз модели на всех данных')

                with gr.Row():
                    mape_mean = gr.Number(label='Средняя абсолютная процентная ошибка (MAPE) в %')
                    mae_mean = gr.Number(label='Средняя абсолютная ошибка')

                with gr.Row():
                    mape_df = gr.Dataframe(headers=["Дата", "mape"],
                                           label='Абсолютная процентная ошибка (MAPE) в %')
                    mae_df = gr.Dataframe(headers=["Дата", "mae"],
                                          label='Aбсолютная ошибка')

                with gr.Row():
                    forecast = gr.Dataframe(headers=["Дата", "Прогноз"],
                                            label='Прогноз')

                with gr.Column():
                    recommendation.click(pipeline,
                                        [ds_col, y_col, steps, validations_steps, trials, temp_file, n_ensemble,
                                         date_border, sheet_name, years, use_save],
                                        [run_id, path, file_output,
                                         val_img, forecast_img,
                                         bins_img, model_forecast_img,
                                         mae_df, mae_mean,
                                         mape_df, mape_mean,
                                         forecast
                                        ])

            with gr.TabItem("Прогнозирование нескольких временных рядов"):
                with gr.Row():
                    sheet_name = gr.Text(label='Название таблицы/листа в excel файле')
                    ds_col = gr.Text(label='Название столбца, в котором находится дата')
                    steps = gr.Number(value=12, precision=0,
                                    label='Количество шагов прогнозирования')
                    validations_steps = gr.Number(value=12, precision=0,
                                                label='Количество шагов для валидации и настройки параметров')
                    trials = gr.Number(value=50, precision=0,
                                    label='Количество запусков настройки гиперпараметров')

                with gr.Row():
                    use_save = gr.Radio(['Нет', 'Да'], value='Да',
                                        label='Использовать сохраненные результаты')
                    date_border = gr.Text(label='Ограничение по дате')
                    years = gr.Number(value=10, precision=0,
                                    label='За сколько последних лет брать данные')

                with gr.Column():
                    temp_file = gr.File(file_types=['.csv', '.xlsx', '.xls'],
                                        label='Файл с данными')

                with gr.Row():
                    recommendation = gr.Button("Начать прогнозирование")

                with gr.Row():
                    run_id = gr.Number(label='id запуска', precision=0)
                    path = gr.Text(label='директория экспериментов')

                with gr.Row():
                    file_output = gr.File(label='Файл с прогнозом')

                with gr.Column():
                    recommendation.click(pipeline_glocal,
                                        [ds_col, steps, validations_steps, trials, temp_file,
                                         date_border, sheet_name, years, use_save],
                                        [run_id, path, file_output])

            with gr.TabItem("Получение результатов из директории"):
                with gr.Row():
                    _id = gr.Number(precision=0,
                                   label='id запуска')
                    path = gr.Text(label='директория результата')

                with gr.Row():
                    recommendation = gr.Button("Начать прогнозирование")

                with gr.Row():
                    file_output = gr.File(label='Файл с прогнозом')

                with gr.Column():
                    with gr.Row():
                        val_img = gr.Image(show_label="")
                        forecast_img = gr.Image(show_label="")
                    with gr.Row():
                        bins_img = gr.Image(show_label="")
                        model_forecast_img = gr.Image(label='Прогноз модели на всех данных')

                with gr.Row():
                    mape_mean = gr.Number(label='Средняя абсолютная процентная ошибка (MAPE) в %')
                    mae_mean = gr.Number(label='Средняя абсолютная ошибка')

                with gr.Row():
                    mape_df = gr.Dataframe(headers=["Дата", "mape"],
                                        label='Абсолютная процентная ошибка (MAPE) в %')
                    mae_df = gr.Dataframe(headers=["Дата", "mae"],
                                        label='Aбсолютная ошибка')

                with gr.Row():
                    forecast = gr.Dataframe(headers=["Дата", "Прогноз"],
                                            label='Прогноз')

                with gr.Column():
                    recommendation.click(get_result,
                                        [_id, path],
                                        [file_output,
                                        val_img, forecast_img,
                                        bins_img, model_forecast_img,
                                        mae_df, mae_mean,
                                        mape_df, mape_mean,
                                        forecast
                                        ])
            with gr.TabItem("Получение результатов для прогнозирования производства"):
                with gr.Row():
                    _id = gr.Number(precision=0,
                                   label='id запуска')
                    path = gr.Text(label='директория результата')

                with gr.Row():
                    recommendation = gr.Button("Начать прогнозирование")

                with gr.Row():
                    file_output = gr.File(label='Архив с прогнозом')

                with gr.Column():
                    recommendation.click(get_result_gl,
                                        [_id, path],
                                        [file_output
                                        ])

            with gr.TabItem("История предыдущих запусков"):
                with gr.Row():
                    rows = gr.Number(precision=0,
                                     label='Количество последних записей')

                with gr.Row():
                    recommendation = gr.Button("Вывести прогнозы")

                with gr.Row():
                    data = gr.Dataframe(headers=['id', 'ds_col', 'y_col', 'steps',
                                                 'file_name', 'sheet_name', 'years',
                                                 'dir_path', 'datetime'],
                                            label='Записи в БД')

                with gr.Column():
                    recommendation.click(db_rows,
                                        [rows],
                                        [data])

    return interface
