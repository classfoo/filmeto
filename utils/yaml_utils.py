from typing import Any

import yaml
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def load_yaml(path):
    try:
        with open(path, 'r', encoding='utf-8') as file:
            data = yaml.safe_load(file)
        return data
    except FileNotFoundError:
        logger.error("file not exists")
    except yaml.YAMLError as e:
        logger.error(f"YAML error: {e}")

def save_yaml(path,dict:Any):
    try:
        with open(path, 'w', encoding='utf-8') as file:
            yaml.safe_dump(dict, file,encoding='utf-8',allow_unicode=True)
    except FileNotFoundError:
        logger.error("file not exists")
    except yaml.YAMLError as e:
        logger.error(f"YAML error: {e}")