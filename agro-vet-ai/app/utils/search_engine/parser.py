import yaml
import glob


def parse_yml_files(directory_path):
    diseases = []
    for file_path in glob.glob(f"{directory_path}/*.yml"):
        with open(file_path, 'r', encoding='utf-8') as file:
            data = yaml.safe_load(file)
            diseases.append(data)
    return diseases
