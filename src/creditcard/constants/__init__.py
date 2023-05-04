from pathlib import Path
import os
from datetime import datetime

def get_current_time_stamp():
    return f"{datetime.now().strftime('%Y%m%d%H%M%S')}"

ROOT_DIR = os.getcwd()
CURRENT_TIME_STAMP = get_current_time_stamp()

CONFIG_DIR = os.path.join(ROOT_DIR,'configs')

CONFIG_FILE_PATH = Path("configs/config.yaml")
PARAMS_FILE_PATH = Path("params.yaml")

DATABASE_FILE_NAME = "database.yaml"
DATABASE_FILE = Path(os.path.join(CONFIG_DIR, DATABASE_FILE_NAME))

FEATURE_GENERATOR_FILE_NAME = "feature_generator.yaml"
FEATURE_GENERATOR_FILE_PATH = Path(os.path.join(CONFIG_DIR, FEATURE_GENERATOR_FILE_NAME))

MODEL_PIPELINE_FILE_NAME = "pipeline.yaml"
MODEL_PIPELINE_FILE_PATH = os.path.join(ROOT_DIR, "Model_Pipeline_Data", MODEL_PIPELINE_FILE_NAME)
