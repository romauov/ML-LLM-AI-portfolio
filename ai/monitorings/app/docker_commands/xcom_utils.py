def docker_xcom_push(data: str) -> None:
    """Выводит данные в stdout с префиксом XCom: для передачи в Airflow XCom.

    CustomDockerOperator считывает stdout контейнера и извлекает данные
    с префиксом 'XCom:' для передачи между задачами Airflow.

    Args:
        data: Строка с данными для передачи в XCom.
    """
    print(f"XCom:{data}")
