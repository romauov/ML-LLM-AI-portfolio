from app.data.handlers.from_database import get_data_from_database
from app.data.handlers.from_excel import get_data_from_exel_file


def get_data_by_config(cfg, date_from=None, date_to=None, file_data=None, for_dashboard=False):
    """
    Загружает данные для предсказания. По входным параметрам определяет необходимую функцию загрузки.
    :param cfg: Config.
    :param date_from: дата начала выборки.
    :param date_to: дата конца выборки.
    :param file_data: dict с параметрами загрузки из excel файла.
    :return: dataframe.
    """
    if file_data:
        return get_data_from_exel_file(
            file_path=file_data['file_path'],
            cfg=cfg,
            sheet_name=file_data['sheet_name'],
            date_column_name=file_data['date'],
            forecast_column_name=file_data['series'],
            history_years_limit=file_data['year_limit'],
        )
    elif date_from:
        return get_data_from_database(date_from, date_to, cfg=cfg, for_dashboard=for_dashboard)
    else:
        raise KeyError('date_from or file_data argument must not be None')
