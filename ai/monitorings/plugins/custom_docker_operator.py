from airflow.plugins_manager import AirflowPlugin

from operators.docker_opearator import *


class CustomDockerOperatorPlugin(AirflowPlugin):
    name = "custom_docker_operator_plugin"
    operators = [CustomDockerOperator]
