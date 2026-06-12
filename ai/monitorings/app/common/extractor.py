import re
import os
from app.utils.data import okrug_map
from app.utils.logger import logger as log


def extract_date_from_file_name(file_path):
    match = re.search(r"(\d{2}\.\d{2}\.\d{2,4})", file_path)
    if match:
        date_str = match.group(1)
        return date_str
    else:
        log.error(f"Could not extract date from {file_path}")
        return None


def extract_federal_okrug_from_file_name(file_path):
    okrug_code_match = re.findall(r'[a-zA-Z]+', os.path.basename(file_path))
    if okrug_code_match:
        for okrug_code in okrug_code_match:
            if okrug_code.lower() in okrug_map:
                return okrug_map[okrug_code.lower()]
        log.error(f"Unknown federal okrug code: {okrug_code_match} in file {file_path}")
        return None
    else:
        log.error(f"Could not extract federal okrug code from {file_path}")
        return None


def get_file_name_by_path(file_path: str, include_parent_name: bool = False) -> str:
    file_name = os.path.basename(file_path)
    if include_parent_name:
        parent_dir_name = os.path.basename(os.path.dirname(file_path))
        return f'{parent_dir_name}/{file_name}'
    else:
        return file_name
