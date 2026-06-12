"""
Визуализация результатов модели

@author Dmitry Abramov
"""

from plotly.subplots import make_subplots
import plotly.graph_objects as go

from .main import farm_modeling

# pylint: disable=too-many-arguments
# Визуализация с помощью плотли
def log_ploting(cow_number: int,
                periods: int,
                rub_per_litr: float,
                korm: float,
                service: float,
                delivery_risk: float,
                conception_risk: float):
    """
    Построение графиков

    Параметры передаются в модель фермы
    """
    if delivery_risk > 1:
        delivery_risk = 1
    elif delivery_risk < 0:
        delivery_risk = 0

    if conception_risk > 1:
        conception_risk = 1
    elif conception_risk < 0:
        conception_risk = 0

    # Датафрейм
    logs, _ = farm_modeling(cow_number,
                            periods,
                            rub_per_litr,
                            korm, service,
                            delivery_risk,
                            conception_risk)
    # Сетка графиков
    fig = make_subplots(rows=3, cols=2,
                        specs=[[{}, {}],
                            [{}, {}],
                            [{'colspan': 2}, None]],
                        subplot_titles=("Удой, кг", "Количество голов",
                                        "Заработок с продажи молока",
                                        "Чистая прибыль по месяцам",
                                        "Доходы/Расходы помесячно", 
                                        "Изменение возраста коров"))

    # График удоев
    fig.add_trace(go.Scatter(x=logs['Удой'].index, y=logs['Удой'],
                line={'color': 'rgb(153,153,255)'},
                name='кг удоя',
                fill='tozeroy',
                legendgroup='1'),
                row=1, col=1)
    # Название осей
    fig['layout']['xaxis']['title']='Дата'
    fig['layout']['yaxis']['title']='кг удоя'

    # Изменение количества скота
    fig.add_trace(go.Scatter(x=logs['Количество_голов'].index, y=logs['Количество_голов'],
                line={'color': 'rgb(180, 151, 231)'},
                name='Количество крс',
                fill='tozeroy',
                legendgroup='1'),
                row=1, col=2)
    fig['layout']['xaxis2']['title']='Дата'
    fig['layout']['yaxis2']['title']='количество голов'

    # Чистая прибыль
    fig.add_trace(go.Scatter(x=logs['Чистая_прибыль'].index, y=logs['Чистая_прибыль'].cumsum(),
                line={'color': 'rgb(153,153,255)'},
                name='Чистая прибыль',
                fill='tozeroy',
                legendgroup='2'),
                row=2, col=1)
    # Доход
    fig.add_trace(go.Scatter(x=logs['Прибыль'].index, y=logs['Прибыль'].cumsum(),
                name='Доход',
                fill='tonexty',
                legendgroup = '2'),
                row=2, col=1)
    fig['layout']['xaxis3']['title']='Дата'
    fig['layout']['yaxis3']['title']='руб'

    # Чистая прибыль помесячно
    fig.add_trace(go.Bar(x=logs['Чистая_прибыль'].index, y=logs['Чистая_прибыль'],
                marker_color='rgb(153,153,255)',
                legendgroup = '2',
                name='Чистая прибыль'),
                row=2, col=2)
    fig['layout']['xaxis4']['title']='Дата'
    fig['layout']['yaxis4']['title']='руб'

    # Доходы/расходы помесячно
    trace1 = go.Bar(x=logs['Прибыль'].index, y=logs['Прибыль'],
                    marker_color='rgb(153,153,255)',
                    legendgroup = '3',
                    name='Доходы')
    trace2 = go.Bar(x=logs['Расходы'].index, y=logs['Расходы'],
                    legendgroup = '3',
                    marker_color='rgb(180, 151, 231)',
                    name='Расходы')
    fig['layout']['xaxis5']['title']='Дата'
    fig['layout']['yaxis5']['title']='руб'

    # Создание сгруппирированной диаграммы
    fig.append_trace(trace1,
                row=3, col=1)
    fig.append_trace(trace2,
                row=3, col=1)

    fig.update_layout(title_text="Моделирование фермерского хозяйства",
                      title_x=0.5,
                      legend_tracegroupgap=460,
                      barmode='group')

    # Размер фигуры
    fig['layout'].update(height=1500, width=1480)

    return fig
