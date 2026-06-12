import os

from airflow.providers.standard.operators.python import PythonOperator
from airflow.providers.standard.sensors.python import PythonSensor
from airflow.sdk import dag
from docker.types import Mount

from operators.docker_opearator import CustomDockerOperator

from constants import CHECK_INTERVAL, SENSOR_TIMEOUT, CONTAINER_TMP, HOST_TMP, HOST_MONS_NEW, HOST_MONS_PROCESSED, \
    HOST_MONS_ERRORS, EXCEL_EXTENSIONS, CONTAINER_MONS_NEW, CONTAINER_MONS_PROCESSED, CONTAINER_MONS_ERRORS
from utils import check_files_exist, collect_files, on_success_move_file, on_failure_move_file, clean_up_temp_files

CONTAINER_EGG_NEW_MONS = os.path.join(CONTAINER_MONS_NEW, 'egg')
CONTAINER_EGG_SUCCESS_MONS = os.path.join(CONTAINER_MONS_PROCESSED, 'egg')
CONTAINER_EGG_ERROR_MONS = os.path.join(CONTAINER_MONS_ERRORS, 'egg')
EGG_MONS_TYPE = 'egg'

dockerops_kwargs = {
    "mount_tmp_dir": False,
    "retries": 1,
    "network_mode": "bridge",
    "xcom_all": True,
    "do_xcom_push": True,
    "image": "app-worker:latest",
    "auto_remove": "force",
    "mounts": [
        Mount(source=HOST_TMP, target=CONTAINER_TMP, type="bind"),
        Mount(source=HOST_MONS_NEW, target=CONTAINER_MONS_NEW, type="bind"),
        Mount(source=HOST_MONS_PROCESSED, target=CONTAINER_MONS_PROCESSED, type="bind"),
        Mount(source=HOST_MONS_ERRORS, target=CONTAINER_MONS_ERRORS, type="bind"),
    ],
}


@dag(
    'egg_excel_pipline',
    catchup=False,
    schedule="0 * * * *",
    params={
        "source_folder": CONTAINER_EGG_NEW_MONS,
        "success_destination": CONTAINER_EGG_SUCCESS_MONS,
        "failure_destination": CONTAINER_EGG_ERROR_MONS,
        "tmp_folder": CONTAINER_TMP
    }
)
def excel_pipline():
    wait_file_checker = PythonSensor(
        task_id='wait_file_appear',
        python_callable=check_files_exist,
        op_args=[CONTAINER_EGG_NEW_MONS, EXCEL_EXTENSIONS],
        timeout=SENSOR_TIMEOUT,
        poke_interval=CHECK_INTERVAL,
        mode="poke",
        soft_fail=True
    )

    collect_files_task = PythonOperator(
        task_id="collect_files", python_callable=collect_files,
        op_args=[CONTAINER_EGG_NEW_MONS, EXCEL_EXTENSIONS], do_xcom_push=True,
    )

    extract_excel_task = CustomDockerOperator.partial(
        task_id="extract_excel",
        on_failure_callback=[on_failure_move_file, clean_up_temp_files],
        trigger_rule="all_done",
        **dockerops_kwargs
    ).expand(
        command=collect_files_task.output.map(
            lambda file_path: f'python -m app.docker_commands.make_process_file '
                              f'--source_file_path {file_path} --monitoring_type {EGG_MONS_TYPE}'
        )
    )

    save_db_task = CustomDockerOperator.partial(
        task_id="save_db",
        on_failure_callback=[on_failure_move_file, clean_up_temp_files],
        on_success_callback=[on_success_move_file, clean_up_temp_files],
        **dockerops_kwargs
    ).expand(
        command=extract_excel_task.output.map(
            lambda args: f'python -m app.docker_commands.make_save_results '
                         f'--source_file_path {args[0]} --df_tmp_file_path {args[1]} '
                         f'--monitoring_type {EGG_MONS_TYPE}'
        )
    )

    wait_file_checker >> collect_files_task >> extract_excel_task >> save_db_task


excel_pipline()
