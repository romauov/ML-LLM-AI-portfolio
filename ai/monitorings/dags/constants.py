import os

# basic times
SECOND = 1
CHECK_INTERVAL = SECOND * 30
SENSOR_TIMEOUT = SECOND * 60 * 2

# airflow docker folders
CONTAINER_TMP = '/opt/airflow/data/'
CONTAINER_MONS = '/opt/airflow/monitoring/'
CONTAINER_MONS_NEW = os.path.join(CONTAINER_MONS, 'new')
CONTAINER_MONS_PROCESSED = os.path.join(CONTAINER_MONS, 'processed')
CONTAINER_MONS_ERRORS = os.path.join(CONTAINER_MONS, 'errors')

# host folders
HOST_MONS_NEW = os.getenv('MONITORING_NEW_FOLDER')
HOST_MONS_PROCESSED = os.getenv('MONITORING_PROCESSED_FOLDER')
HOST_MONS_ERRORS = os.getenv('MONITORING_ERRORS_FOLDER')
HOST_TMP = os.getenv('TMP_FILES_FOLDER')

# other
EXCEL_EXTENSIONS = (".xlsx", ".xls")
CSV_EXTENSIONS = (".csv",)
