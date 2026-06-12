"""
Конфигурация логирования для TimesFM-воркера.

@author Dmitry Avzalov
"""

import logging

log = logging.getLogger()
log.setLevel(logging.INFO)
console_handler = logging.StreamHandler()
file_handler = logging.FileHandler('storage/timesfm-worker.log')

logging.getLogger('py.warnings').disabled = True

formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
console_handler.setFormatter(formatter)
file_handler.setFormatter(formatter)

log.addHandler(console_handler)
log.addHandler(file_handler)
