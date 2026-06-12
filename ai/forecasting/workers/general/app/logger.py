import logging
import warnings

from prophet.forecaster import logger as prophet_logger

warnings.filterwarnings("ignore", category=UserWarning)
warnings.filterwarnings("ignore", category=RuntimeWarning)
warnings.filterwarnings("ignore", category=FutureWarning)

log = logging.getLogger()
log.setLevel(logging.INFO)
console_handler = logging.StreamHandler()
file_handler = logging.FileHandler('storage/common-worker.log')

logging.getLogger('py.warnings').disabled = True

# disable prophet logs
prophet_logger.setLevel('ERROR')
logging.getLogger('cmdstanpy').disabled = True

formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
console_handler.setFormatter(formatter)
file_handler.setFormatter(formatter)

log.addHandler(console_handler)
log.addHandler(file_handler)
