import os
import sys
from pathlib import Path

from  creditcard.constants import (CURRENT_TIME_STAMP, ROOT_DIR)
from  creditcard.entity.config_entity import (DataIngestionConfig, DataTransformationConfig,
                               DataValidationConfig, TrainingPipelineConfig, ModelTrainerConfig, ModelEvaluationConfig,
                               ModelPusherConfig)
from  creditcard.exception import AppException
from  creditcard.logger import logger
from  creditcard.utils.common import create_directories, read_yaml
from creditcard.constants import CONFIG_FILE_PATH


class ConfigurationManager:

    def __init__(self, config_file_path: Path = CONFIG_FILE_PATH ) -> None:
        """ Configuration manager class to read the configuration file and create the configuration objects.
        Args:
            config_file_path (Path, optional): _description_. Defaults to CONFIG_FILE_PATH.
        Raises:
            AppException: _description_ if the configuration file is not found or if the configuration file is not
            in the correct format.
        """

        try:
            self.config_info = read_yaml(path_to_yaml=Path(config_file_path))
            self.pipeline_config = self.get_training_pipeline_config()
            self.time_stamp = CURRENT_TIME_STAMP

        except Exception as e:
            raise AppException(e, sys) from e

    def get_data_ingestion_config(self) -> DataIngestionConfig:
        """ Get the data ingestion configuration object.
        Raises:
            AppException: _description_
        Returns:
            DataIngestionConfig:  Pydanctic base model data ingestion configuration object. 
            dataset_download_id: str
            raw_data_file_path: Path
            ingested_train_file_path: Path
            ingested_test_data_path: Path
            random_state: int     """

        try:
            logger.info("Getting data ingestion configuration.")
            data_ingestion_info = self.config_info.data_ingestion_config
            pipeline_config = self.pipeline_config
            artifact_dir = pipeline_config.artifact_dir
            random_state = pipeline_config.training_random_state
            dataset_download_id = data_ingestion_info.dataset_download_id
            data_ingestion_dir_name = data_ingestion_info.ingestion_dir
            raw_data_dir = data_ingestion_info.raw_data_dir
            raw_file_name = data_ingestion_info.dataset_download_file_name

            data_ingestion_dir = os.path.join(artifact_dir, data_ingestion_dir_name)
            raw_data_file_path = os.path.join(data_ingestion_dir, raw_data_dir, raw_file_name)
            ingested_dir_name = data_ingestion_info.ingested_dir
            ingested_dir_path = os.path.join(data_ingestion_dir, ingested_dir_name)

            ingested_train_file_path = os.path.join(ingested_dir_path, data_ingestion_info.ingested_train_file)
            ingested_test_file_path = os.path.join(ingested_dir_path, data_ingestion_info.ingested_test_file)
            create_directories([os.path.dirname(raw_data_file_path), os.path.dirname(ingested_train_file_path)])

            data_ingestion_config = DataIngestionConfig(dataset_download_id=dataset_download_id,
                                                        raw_data_file_path=raw_data_file_path,
                                                        ingested_train_file_path=ingested_train_file_path,
                                                        ingested_test_data_path=ingested_test_file_path,
                                                        random_state=random_state)
            logger.info(f"Data ingestion config: {data_ingestion_config.dict()}")
            logger.info("Data ingestion configuration completed.")

            return data_ingestion_config
        except Exception as e:
            raise AppException(e, sys) from e

    def get_training_pipeline_config(self) -> TrainingPipelineConfig:
        """ Get the training pipeline configuration object.
        class TrainingPipelineConfig(BaseModel):
                artifact_dir: DirectoryPath
                training_random_state: int
                pipeline_name: str
                experiment_code: str
        
        """
        try:
            training_config = self.config_info.training_pipeline_config
            training_pipeline_name = training_config.pipeline_name
            training_experiment_code = training_config.experiment_code
            training_random_state = training_config.random_state
            training_artifacts = os.path.join(ROOT_DIR, training_config.artifact_dir)
            create_directories(path_to_directories=[training_artifacts])
            training_pipeline_config = TrainingPipelineConfig(artifact_dir=training_artifacts,
                                                              experiment_code=training_experiment_code,
                                                              pipeline_name=training_pipeline_name,
                                                              training_random_state=training_random_state)
            logger.info(f"Training pipeline config: {training_pipeline_config}")
            return training_pipeline_config
        except Exception as e:
            raise AppException(e, sys) from e
        

    def get_data_validation_config(self, schema_file_path: Path , data_ingestion_config  : DataIngestionConfig) -> DataValidationConfig:
        """ Get the data validation configuration object.
        Args:
            schema_file_path (Path):  Path( "configs/schema.yaml")
        Raises:
            AppException: _description_
        Returns:
            DataValidationConfig:  class DataValidationConfig(BaseModel):
                                    schema_file_path: FilePath
                                    report_file_dir: Path
                                    data_validated_test_file_path: Path
                                    data_validated_train_path: Path
                                    train_data_file: FilePath
                                    test_data_file: FilePath """
        try:
            logger.info("Getting data validation configuration.")
            pipeline_config = self.pipeline_config
            artifact_dir = pipeline_config.artifact_dir
            train_data_file = data_ingestion_config.ingested_train_file_path
            test_data_file = data_ingestion_config.ingested_test_data_path
            data_validation_config_info = self.config_info.data_validation_config
            validated_test_file_name = data_validation_config_info.validated_test_file
            validated_train_file_name = data_validation_config_info.validated_train_file

            data_validated_artifact_dir = Path(
                os.path.join(artifact_dir, data_validation_config_info.data_validation_dir))
            report_file_dir = os.path.join(data_validated_artifact_dir, data_validation_config_info.report_dir)
            validated_test_file = os.path.join(data_validated_artifact_dir, validated_test_file_name)
            validated_train_file = os.path.join(data_validated_artifact_dir, validated_train_file_name)

            create_directories([report_file_dir])

            data_validation_config = DataValidationConfig(schema_file_path=schema_file_path,
                                                          report_file_dir=report_file_dir,
                                                          data_validated_test_file_path=validated_test_file,
                                                          data_validated_train_file_path=validated_train_file,
                                                          train_data_file=train_data_file,
                                                          test_data_file=test_data_file)
            logger.info(f"Data validation config: {data_validation_config.dict()}")
            return data_validation_config

        except Exception as e:
            raise AppException(e, sys)
        

    def get_data_transformation_config(self, feature_generator_config_file_path: Path,
                                       schema_file_path : Path , data_validation_config_info : DataValidationConfig ) -> DataTransformationConfig:
        """ Get the data transformation configuration object.
        Args:
            feature_generator_config_file_path (Path): config file path to generate features
            schema_file_path (_type_):  schema file path to validate data
        Raises:
            AppException: _description_
        Returns:
            DataTransformationConfig: class DataTransformationConfig(BaseModel):
                                            data_validated_train_file_path: FilePath
                                            feature_generator_config_file_path: FilePath
                                            schema_file_path: FilePath
                                            preprocessed_object_file_path: Path
                                            random_state: int
        """
        try:
            pipeline_config = self.pipeline_config
            artifact_dir = pipeline_config.artifact_dir
            random_state = pipeline_config.training_random_state
            schema_file_path = data_validation_config_info.schema_file_path
            data_transformation_config_info = self.config_info.data_transformation_config

            data_transformation_dir_name = data_transformation_config_info.data_transformation_dir
            data_transformation_dir = os.path.join(artifact_dir, data_transformation_dir_name)
            preprocessed_object_dir = data_transformation_config_info.preprocessing_object_dir
            preprocessed_object_name = data_transformation_config_info.preprocessing_object_file_name
            preprocessed_object_file_path = os.path.join(data_transformation_dir, preprocessed_object_dir,
                                                         preprocessed_object_name)

            create_directories([os.path.dirname(preprocessed_object_file_path)])
            data_transformation_config = DataTransformationConfig(
                data_validated_train_file_path=data_validation_config_info.data_validated_train_file_path,
                feature_generator_config_file_path=feature_generator_config_file_path,
                schema_file_path=schema_file_path,
                preprocessed_object_file_path=preprocessed_object_file_path,
                random_state=random_state)
            return data_transformation_config
        except Exception as e:
            raise AppException(e, sys)
