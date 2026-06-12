from typing import Any, List, Optional, Union

from airflow.providers.docker.exceptions import (
    DockerContainerFailedException,
    DockerContainerFailedSkipException,
)
from airflow.providers.docker.operators.docker import DockerOperator
from airflow.sdk import Context


class CustomDockerOperator(DockerOperator):
    """
    DockerOperator, который всегда сохраняет stdout контейнера в XCom,
    даже если выполнение завершилось ошибкой.

    Основные отличия от стандартного DockerOperator:
    1. Логи сохраняются в XCom при любом исходе выполнения (успех/ошибка).
    2. Для вывода можно задать кастомный ключ через параметр `xcom_key` (по умолчанию "return_value").
    3. Работает с параметрами `xcom_all` и `do_xcom_push` для контроля формата вывода.
    """

    def __init__(self, xcom_key: str = "return_value", **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.xcom_key = xcom_key

    def _push_logs_to_xcom(self, context: Context, logs: List[str]) -> None:
        """Отправляет логи контейнера в XCom, если включена соответствующая опция."""
        if not getattr(self, "do_xcom_push", False):
            return

        elif getattr(self, "xcom_all", False):
            result_to_push = logs
        else:
            result_to_push = [logs[-1]]

        # пушим в хранилище только логи с специальным префиксом 'XCom:'
        values = []
        for result in result_to_push:
            if result.startswith('XCom:'):
                data = result[5:]
                values.append(data)
        if values:
            context["ti"].xcom_push(key=self.xcom_key, value=values)

    def execute(self, context: Context) -> Optional[Union[str, List[str]]]:
        """
        Запускает контейнер, перехватывает исключения, связанные с ошибками контейнера,
        и гарантирует сохранение логов в XCom перед тем, как пробросить исключение дальше.
        """

        try:
            result = super().execute(context)

        # отлавливаем завершение контейнера с ошибкой
        except (DockerContainerFailedException, DockerContainerFailedSkipException) as e:
            logs = getattr(e, "logs")
            if logs:
                self._push_logs_to_xcom(context, logs)

                if self.on_failure_callback:
                    for callback in self.on_failure_callback:
                        try:
                            callback(context)
                        except Exception as e:
                            print(e)
            raise

        except Exception:
            self.log.exception("Unexpected error during DockerOperator execution")
            raise

        else:
            if result:
                if isinstance(result, list):
                    logs = result
                else:
                    logs = [str(result)]
                self._push_logs_to_xcom(context, logs)
        return None
