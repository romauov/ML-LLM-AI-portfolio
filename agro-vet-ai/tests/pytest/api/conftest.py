import json
import os
import pytest
from dotenv import load_dotenv

import logger

load_dotenv()

API_KEY = os.getenv("API_KEY")
API_SERVICE_HOST_PORT = os.getenv("API_SERVICE_HOST_PORT")
BASE_URL = f"http://localhost:{API_SERVICE_HOST_PORT}"

if not API_KEY:
    raise ValueError("API_KEY environment variable is not set")
if not API_SERVICE_HOST_PORT:
    raise ValueError("API_SERVICE_HOST_PORT environment variable is not set")

HEADERS = {"Authorization": f"Bearer {API_KEY}"}


def pytest_addoption(parser):
    parser.addoption("--model", default=None, help="Модель для тестов (по умолчанию — как в API)")


@pytest.fixture
def api_config(request):
    config = {"base_url": BASE_URL, "headers": HEADERS}
    model = request.config.getoption("--model")
    if model:
        config["model"] = model
    return config


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    if call.when == "call":
        extra = logger.flush()
        if extra:
            outcome.get_result().user_properties.append(
                ("_log_extra", json.dumps(extra, ensure_ascii=False))
            )


def pytest_sessionstart(session):
    if hasattr(session.config, "workerinput"):
        return
    logger.open_session()


def pytest_runtest_logreport(report):
    if report.when != "call":
        return
    status = "PASSED" if report.passed else "FAILED" if report.failed else "ERROR"
    extra_raw = next((v for k, v in report.user_properties if k == "_log_extra"), "{}")
    extra = json.loads(extra_raw)
    longrepr = str(report.longrepr) if report.failed else ""
    logger.log_result(report.nodeid, status, report.duration, longrepr, extra)


def pytest_sessionfinish(session, exitstatus):
    if hasattr(session.config, "workerinput"):
        return
    logger.close_session(exitstatus)
