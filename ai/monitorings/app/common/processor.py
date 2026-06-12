from typing import Optional

import pandas as pd
import re


def process_price(price):
    """
    Преобразует строку цены в число с плавающей запятой, обрабатывая различные форматы и возможные ошибки.

    Args:
        price (str or float): Значение цены для преобразования.
output_dir
    Returns:
        float or None: Цена в виде числа с плавающей запятой или None, если преобразование не удалось.
    """
    if pd.isna(price):
        return None
    price_str = str(price).replace('р.', '').replace(',', '.').strip()
    try:
        return float(price_str)
    except ValueError:
        print(f"Не удалось преобразовать значение: {price}")
        return None


def process_weighted_price(price: str) -> Optional[float]:
    if pd.isna(price):
        return None
    match = re.match(r'-?\d*(\.|\,)?\d+', price)
    if match:
        try:
            found_price = float(match.group(0))
            return found_price if found_price != 0 else None
        except ValueError:
            print(f"Не удалось преобразовать значение: {price}")
            return
    return
