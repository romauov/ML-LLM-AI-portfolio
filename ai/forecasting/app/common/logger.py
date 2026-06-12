"""
Модуль логирования.
Дополнительно перенаправлены логи optuna и отключены логи интерактивных графиков neuralprophet.

@author Nikolay Zhabchikov
"""
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

console_handler = logging.StreamHandler()
file_handler = logging.FileHandler('storage/forecasting.log')

# disable interactive plot errors
logging.getLogger("NP.plotly").disabled = True
logging.getLogger('py.warnings').disabled = True

formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
console_handler.setFormatter(formatter)
file_handler.setFormatter(formatter)

logger.addHandler(console_handler)
logger.addHandler(file_handler)
