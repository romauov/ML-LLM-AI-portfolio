"""
Логирование пайплайна мониториинга мониторинга

@author Sergei Romanov
"""
import logging
import time

logger = logging.getLogger()
logger.setLevel(logging.INFO)

console_handler = logging.StreamHandler()

logging.getLogger("nltk").setLevel(logging.WARNING)
logging.getLogger("NP.plotly").disabled = True
logging.getLogger('py.warnings').disabled = True

formatter = logging.Formatter(
    '%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S')
console_handler.setFormatter(formatter)

logger.addHandler(console_handler)


def log_traceback(traceback_error_string, error):
    """запись трейсбэка с ошибкой в лог

    Args:
        traceback_error_string (str): traceback
        error (Exception, optional): вид ошибки. Defaults to ''.
        message (str, optional): текст сообщения, приведшего к ошибке. Defaults to ''.
    """
    with open("errors.log", "a") as myfile:
        myfile.write("\r\n\r\n" +
                     time.strftime("%c") +
                     "\r\n<<ERROR>>\r\n" +
                     f'{error}' +
                     "\r\n<<TRACEBACK>>\r\n" +
                     traceback_error_string
                     )
