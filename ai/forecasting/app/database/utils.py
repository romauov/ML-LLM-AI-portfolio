from typing import List

from app.common.constants import INDICATORS_COL_MAPPING
from app.common.enums import ProductsType
from app.common.settings import secrets as s
from config.configs import CommonSeaFoodProduct, CommonMeatProduct

db_raw_seafood_table_name = s.db_raw_seafood_table_name
db_raw_caviar_table_name = s.db_raw_caviar_table_name
db_raw_fish_table_name = s.db_raw_fish_table_name
db_raw_shrimp_table_name = s.db_raw_shrimp_table_name
db_raw_semiprocessed_table_name = s.db_raw_semiprocessed_table_name


def _dict_value_to_sql(key, value):
    if '%' in value:
        value = value.replace('%', '%%')
        return f"{key} like '{value}'"
    else:
        return f"{key} = '{value}'"


def product_config_to_sql_conditions(config: List[CommonSeaFoodProduct | CommonMeatProduct]):
    sql_where_conditions = []

    for product in config:
        sub_requests = []
        for keys, values in product:
            if values and keys != 'name':
                handled_values = []
                for value in values:
                    if value is None:
                        handled_value = f"{keys} is NULL"
                    else:
                        handled_value = _dict_value_to_sql(keys, value)

                    handled_values.append(handled_value)

                sub_request = f"({' OR '.join(handled_values)})"
                sub_requests.append(sub_request)

        request = ' AND '.join(sub_requests)
        sql_where_conditions.append(f"({request})")

    return sql_where_conditions


def get_seafood_table_and_columns_by_type(products_type: ProductsType):
    if products_type == ProductsType.seafood:
        columns = 'product_type, goods_type, cutting'
        table = db_raw_seafood_table_name
    elif products_type == ProductsType.caviar:
        columns = 'product_type, product_class'
        table = db_raw_caviar_table_name
    elif products_type == ProductsType.fish:
        columns = 'fish_type, product_type, cutting'
        table = db_raw_fish_table_name
    elif products_type == ProductsType.shrimp:
        columns = 'product_type, cutting'
        table = db_raw_shrimp_table_name
    elif products_type == ProductsType.semiprocessed:
        columns = 'fish_type, cook_method, cutting, filling, boxing'
        table = db_raw_semiprocessed_table_name
    else:
        raise KeyError('Unknown ProductsType')

    return table, columns


def make_sql_request_from_table_metadata(metadata_df, indicator_id):
    """
    Подготовка select sql запроса к таблицам индикаторам по датафрейму с структурой.
    :param metadata_df:
    :param indicator_id:
    :return: str: sql запрос.
    """
    metadata_df = metadata_df.sort_values('position', axis=0)

    cols = []
    for _, row in metadata_df.iterrows():
        id_ = row['id']
        title = INDICATORS_COL_MAPPING.get(row["name"], row["name"])
        title = title.replace(" ", "_").replace("(", "").replace(")", "")
        cols.append(f'column_{id_} as {title}')

    sql_request = f"select {', '.join(cols)} from indicator_data_{indicator_id}"
    return sql_request
