import os
import sys
import warnings
from pathlib import Path

from creditcard.constants import CURRENT_TIME_STAMP, MODEL_PIPELINE_FILE_PATH
from creditcard.config.configuration import ConfigurationManager
from creditcard.components import DataIngestion,DataValidation,DataTransformation,ModelTrainer
from creditcard.entity.artifact_entity import *
from creditcard.entity.config_entity import *
from creditcard.exception import AppException
from creditcard.utils.common import write_yaml, read_yaml_as_dict,read_yaml
from creditcard.logger import logger
from sklearn import set_config

warnings.filterwarnings("ignore")
set_config(transform_output="pandas")


class ApplicationPipeline:
    model_status = False

    def __init__(self, model_pipeline_data_path=MODEL_PIPELINE_FILE_PATH) -> None:

        self.model_pipeline_data_path = model_pipeline_data_path
        self.time_stamp = CURRENT_TIME_STAMP
        self.config = ConfigurationManager()
        self.model_artifact_dict = dict()

    def update_pipeline_status(self, data: dict):
        data_to_insert = data
        master_key = data_to_insert["start_time"]
        del data_to_insert["start_time"]
        master_data = {master_key: data_to_insert}

        pipeline_data_path = self.model_pipeline_data_path
        if os.path.exists(pipeline_data_path):
            reference = read_yaml_as_dict(path_to_yaml=Path(pipeline_data_path))
            master_data.update(reference)
        write_yaml(file_path=Path(pipeline_data_path), data=master_data)
        ApplicationPipeline.model_status = False
        return "Pipeline is complete"

    def run_pipeline(self):
        running_dict = dict()
        status = ApplicationPipeline.model_status
        if status:
            return "Model pipeline is Training"
        else:
            try:
                running_dict["start_time"] = CURRENT_TIME_STAMP
                logger.info("Pipeline started")
                ApplicationPipeline.model_status = True
                running_dict["status"] = True
                logger.info("data ingestion started")
                data_ingestion_config = self.config.get_data_ingestion_config()
                data_ingestion = DataIngestion(data_ingestion_config_info=data_ingestion_config)
                data_ingestion_response = data_ingestion.initiate_data_ingestion()
                running_dict.update(data_ingestion_response.dict())
                logger.info("data ingestion finished")
                logger.info("data validation started")
                data_validation_config = self.config.get_data_validation_config()
                data_ingestion = DataValidation(data_validation_config_info=data_validation_config)
                data_ingestion_response = data_ingestion.initiate_data_validation()
                logger.info("data validation  finished")
                logger.info("data transformation started")
                data_transformation_config = self.config.get_data_transformation_config()
                data_transformation = DataTransformation(data_transformation_config_info=data_transformation_config)
                data_transformation_response = data_transformation.initiate_data_transformation()
                running_dict.update(data_transformation_response.dict())
                logger.info("data transformation Finished")
                logger.info("Model trainer started")
                model_trainer_config_info = self.config.get_model_trainer_config()
                model_trainer = ModelTrainer(model_trainer_config_info=model_trainer_config_info)
                model_trainer_response = model_trainer.initiate_model_trainer()
                running_dict.update(model_trainer_response.dict())
                logger.info("Model trainer Finished")
                
            except Exception as e:
                raise AppException(e, sys) from e


if __name__ == "__main__":
    pipeline = ApplicationPipeline()

    pipeline_status = pipeline.run_pipeline()