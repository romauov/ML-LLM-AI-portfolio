import json
import re
import threading
from datetime import datetime
from pathlib import Path

_LOG_BASE = Path(__file__).parent / "logs"
_lock = threading.Lock()
_file = None
_records: list[dict] = []
_tls = threading.local()


def open_session() -> None:
    global _file, _records
    now = datetime.now()
    log_dir = _LOG_BASE / now.strftime("%Y-%m-%d")
    log_dir.mkdir(parents=True, exist_ok=True)
    log_path = log_dir / f"{now.strftime('%H-%M-%S')}.json"
    _file = log_path.open("w", encoding="utf-8")
    _records = []


def update(**kwargs) -> None:
    if not hasattr(_tls, "data"):
        _tls.data = {}
    _tls.data.update(kwargs)


def flush() -> dict:
    data = getattr(_tls, "data", {})
    _tls.data = {}
    return data


def _extract_assertion(longrepr: str) -> str | None:
    if not longrepr:
        return None
    lines = longrepr.splitlines()
    error_lines = [l[2:].strip() for l in lines if l.strip().startswith("E ")]
    ref_lines = [l.strip() for l in lines if re.search(r"\.py:\d+:", l)]
    parts = "\n".join(error_lines)
    if ref_lines:
        parts += "\n" + ref_lines[-1]
    return parts or longrepr[:600]


def log_result(nodeid: str, status: str, duration: float, longrepr: str, extra: dict) -> None:
    if _file is None:
        return
    parts = nodeid.split("::")
    test_group = parts[-2] if len(parts) >= 3 else ""
    test_case = parts[-1] if len(parts) >= 2 else nodeid
    is_technical = status != "PASSED" and bool(
        longrepr and re.search(r"embeddings API|Embeddings API|Статус \d+|ConnectionError", longrepr)
    )
    record = {
        "test_group": test_group,
        "test_case": test_case,
        "query": extra.get("query"),
        "agent_response": extra.get("agent_response"),
        "reference_answer": extra.get("reference_answer"),
        "cosine_similarity": extra.get("cosine_similarity"),
        "status": status,
        "error": 1 if is_technical else 0,
        "assertion_message": _extract_assertion(longrepr) if status != "PASSED" else None,
        "query_processing_duration": extra.get("query_processing_duration"),
        "test_duration": round(duration, 1),
    }
    with _lock:
        _records.append(record)
        _file.seek(0)
        json.dump(_records, _file, ensure_ascii=False, indent=2)
        _file.truncate()
        _file.flush()


def close_session(exitstatus) -> None:
    global _file
    if _file is None:
        return
    _file.close()
    _file = None
