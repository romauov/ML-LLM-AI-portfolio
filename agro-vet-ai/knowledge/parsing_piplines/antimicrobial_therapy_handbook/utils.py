import json
import os.path

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__)))


def get_handbook_keywords() -> list[str]:
    file_path = os.path.join(PROJECT_ROOT, 'key_terms.json')
    with open(file_path, 'r') as f:
        data = json.load(f)

    return data
