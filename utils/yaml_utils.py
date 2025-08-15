from typing import Any

import yaml
from pathlib import Path


def load_yaml(path):
    try:
        with open(path, 'r', encoding='utf-8') as file:
            data = yaml.safe_load(file)
        return data
    except FileNotFoundError:
        print("file not exists")
    except yaml.YAMLError as e:
        print(f"YAML error: {e}")

def save_yaml(path,dict:Any):
    try:
        with open(path, 'w', encoding='utf-8') as file:
            yaml.safe_dump(dict, file,encoding='utf-8',allow_unicode=True)
    except FileNotFoundError:
        print("file not exists")
    except yaml.YAMLError as e:
        print(f"YAML error: {e}")