"""
Диграмма возрастов

@author Dmitry Abramov
"""
from plotly.subplots import make_subplots
import plotly.graph_objects as go

from .main import farm_modeling
# pylint: disable=too-many-arguments
def check_age_plot(cow_number: int,
                   periods: int,
                   rub_per_litr: float,
                   korm: float,
                   service: float,
                   delivery_risk: float,
                   conception_risk: float):
    """
    Интерактивный график возрастов
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
    _, ages = farm_modeling(cow_number,
                            periods,
                            rub_per_litr,
                            korm,
                            service,
                            delivery_risk,
                            conception_risk)

    fig = make_subplots(rows=1, cols=2,
                        specs=[[{'colspan': 2}, None]])
    # Подготовка датафрема
    ages['Date'] = ages.index
    ages = ages.melt(id_vars=["Date"],
                     var_name="age",
                     value_name="count")

    trace3 = go.Bar(x=ages[ages['Date'] == ages['Date'][0]]['age'],
                        y=ages[ages['Date'] == ages['Date'][0]]['count'],
                        marker_color='rgb(153,153,255)')
    fig.add_trace(trace3,
                row=1, col=1)
    # Инициализация кадров
    frames = []
    for date in ages['Date'].unique():
        period = ages[ages['Date'] == date]

        frames.append(
            go.Frame(
                name=str(date),
                data=[
                    go.Bar(x=period['age'],
                           y=period['count']),
                ],
            )
        )
    # Создание фигуры
    fig = go.Figure(data=fig.data, frames=frames, layout=fig.layout)

    # Полоска
    fig.update_layout(
        sliders=[
            {
                "active": 0,
                "currentvalue": {"prefix": "Дата="},
                "len": 0.8,
                "steps": [
                    {
                        "args": [
                            [fr.name],
                            {
                                "frame": {"duration": 20, "redraw": True},
                                "mode": "immediate",
                                "fromcurrent": True,
                            },
                        ],
                        "label": fr.name,
                        "method": "animate",
                    }
                    for fr in fig.frames
                ],
            }
        ],
    )
    # Скейлинг оси у
    go.Figure(
        data=fig.data,
        frames=[
            fr.update(
                layout={
                    "yaxis": {"range": [min(fr.data[0].y), max(fr.data[0].y) + 0.1]},
                }
            )
            for fr in fig.frames
        ],
        layout=fig.layout
    )
    # Кнопки
    fig["layout"]["updatemenus"] = [
    {
        "buttons": [
            {
                "args": [None, {"frame": {"duration": 1000, "redraw": False},
                                "fromcurrent": True, "transition": {"duration": 50,
                                                                    "easing": "quadratic-in-out"}}],
                "label": "Play",
                "method": "animate"
            },
            {
                "args": [[None], {"frame": {"duration": 10, "redraw": False},
                                  "mode": "immediate",
                                  "transition": {"duration": 20}}],
                "label": "Pause",
                "method": "animate"
            }
        ],
        "direction": "left",
        "pad": {"r": 10, "t": 87},
        "showactive": False,
        "type": "buttons",
        "x": 0.03,
        "xanchor": "right",
        "y": 0.03,
        "yanchor": "top"
    }]

    # Размер фигуры
    fig['layout'].update(height=600, width=1480)
    fig['layout']['xaxis']['title'] = 'Возраст'
    fig['layout']['yaxis']['title'] = 'Количество голов'
    fig['layout']['sliders'][0]['pad'] = {'l': 70}

    return fig
