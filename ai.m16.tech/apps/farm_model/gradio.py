"""
Интерфейс для модели

@author Dmitry Abramov
"""
import gradio as gr

from .visualize_logs import log_ploting
from .visualize_ages import check_age_plot


def gr_farm_interface():
    """
    Интерфейс для фермы
    """
    with gr.Blocks() as farm:
        with gr.Column():
            with gr.Row():
                # pylint: disable=line-too-long
                gr.Markdown(
                    """
                    # <center>Модель молочной фермы</center>
                    ##### Что способна учитывать модель и использованные допущения

                       №  | Признак  | № | Признак
                       -- | -------- | -- | -------
                       1  | Рождение коров, быки отбрасываются | 6  | Зачатие может пройти неуспешно, также теленок может умереть при родах
                       2  | Ежемесячный удой, каждый день корова даёт разное <br>количество молока, моделируется по нормальному распределению | 7  | Корова способна давать молоко только в течение 10 месяцев после успешных родов
                       3  | Каждая корова даёт в среднем 5500 кг молока в год | 8  | Расходы одинаковые на каждую корову
                       4  | При достижении 15 лет корова умирает и удаляется из фермы | 9  | Нет учета болезней
                       5  | Изначальный возраст коров от 1 до 13 лет | 10  | Нет учета продажи коровы на мясо
                    """
                )
            # Получение значений
            with gr.Row():
                krc_number = gr.Number(value=30, precision=0,
                                       label='Количество коров')
                period = gr.Number(value=20, precision=0,
                                   label='Период моделирования')
                rub_per_litr = gr.Number(value=50,
                                         label='Стоимость литра молока')
            with gr.Row():
                korm_month = gr.Number(value=1500,
                                       label='корм для каждой коровы, руб/мес')
                service = gr.Number(value=2000,
                                    label='дополнительные расходы на каждую корову, руб/мес')
            with gr.Row():
                delivery_risk = gr.Number(value=0.9,
                                          label='Вероятность успешного рождения')
                conception_risk = gr.Number(value=0.9,
                                            label='Вероятность успешного зачатия')


            with gr.Row():
                btn = gr.Button(value="Обновить диаграммы")

            with gr.Tabs():
                with gr.TabItem("Диаграмма удоев и прибыли"):
                    result = gr.Plot(label='Диагрaммы').style()
                    farm.load(log_ploting, [krc_number, period, rub_per_litr, korm_month,
                                            service, delivery_risk, conception_risk], result)
                    btn.click(log_ploting, [krc_number, period, rub_per_litr, korm_month,
                                            service, delivery_risk, conception_risk], result)

                with gr.TabItem("Изменение возрастов"):
                    result = gr.Plot().style()
                    farm.load(check_age_plot, [krc_number, period, rub_per_litr, korm_month,
                                               service, delivery_risk, conception_risk], result)
                    btn.click(check_age_plot, [krc_number, period, rub_per_litr, korm_month,
                                               service, delivery_risk, conception_risk], result)

    return farm
