import logging
import warnings

warnings.filterwarnings("ignore", category=FutureWarning)

log = logging.getLogger()
log.setLevel(logging.INFO)
console_handler = logging.StreamHandler()
file_handler = logging.FileHandler('storage/arima-worker.log')

formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
console_handler.setFormatter(formatter)
file_handler.setFormatter(formatter)

log.addHandler(console_handler)
log.addHandler(file_handler)
