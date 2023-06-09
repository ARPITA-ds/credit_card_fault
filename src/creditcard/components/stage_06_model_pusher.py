import argparse
import os
import sys
import warnings
from pathlib import Path
from box import ConfigBox

import pandas
import numpy

from creditcard.config.configuration import ConfigurationManager
from creditcard.entity import (ModelEvaluationArtifact,
                               ModelPusherArtifact, ModelPusherConfig)
from creditcard.entity.artifact_entity import MetricEvalArtifact
from creditcard.exception import AppException
from creditcard.logger import logger
from creditcard.utils import (evaluate_classification_model, load_object,
                              read_yaml, save_object)
from creditcard.utils.common import read_yaml_as_dict, write_json, write_yaml

warnings.filterwarnings("ignore")


class ModelPusher:

    def __init__(self, model_pusher_config: ModelPusherConfig,
                 model_evaluation_artifact: ModelEvaluationArtifact = None):
        try:
            logger.info(f"{'>>' * 30}Model Pusher log started.{'<<' * 30} ")
            self.model_pusher_config = model_pusher_config
            self.model_evaluation_artifact = model_evaluation_artifact
            self.train_df =  pandas.read_pickle(self.model_pusher_config.validated_train_path)
            self.test_df = pandas.read_pickle(self.model_pusher_config.validated_test_path)
            self.schema = read_yaml(path_to_yaml=Path(self.model_pusher_config.schema_file_path))

        except Exception as e:
            raise AppException(e, sys) from e
    def get_updated_model_status(self, report_obj: object, config_file_path: Path, eval_model_dir: Path):

        is_model_accepted = False
        config_info = read_yaml_as_dict(path_to_yaml=Path(config_file_path))
        report_data = ConfigBox(report_obj.as_dict())
        test_data_result = report_data.metrics[0].result.current
        train_data_result = report_data.metrics[0].result.reference
        test_json = {f"test_{key}": data for key, data in test_data_result.items()}
        train_json = {f"train_{key}": data for key, data in train_data_result.items()}
        data_to_dump = {**test_json, **train_json}
        logger.info(data_to_dump)
        logger.info(type(data_to_dump))
        metrics_path = os.path.join(eval_model_dir, "model_eval_report.json")
        logger.info(f"metrics_path : {metrics_path}")
        write_json(data_to_dump=data_to_dump, file_path=Path(metrics_path))
        base_accuracy = float(config_info["model_pusher_config"]["base_accuracy"])
        test_accuracy = float(test_data_result["accuracy"])
        if test_accuracy > base_accuracy:
            is_model_accepted = True
            logger.info(f" model accepted_status {is_model_accepted}")
            config_info["model_pusher_config"]["base_accuracy"] = test_accuracy
            logger.info(f"update config path {config_file_path} ")
            update_config_path = os.path.join(os.getcwd(), config_file_path)
            write_yaml(file_path=Path(update_config_path), data=config_info)
            logger.info("config updated")
        return is_model_accepted

    def initiate_model_pusher(self) -> ModelPusherArtifact:
        try:
            best_eval_model = None
            best_model_path_reference = self.model_pusher_config.production_model_path
            eval_best_model = load_object(file_path = Path(self.model_pusher_config.evaluated_model_path))
            if not os.path.exists(best_model_path_reference):
                model_list = [eval_best_model]
            else:
                best_current_model = load_object(file_path=Path(best_model_path_reference))
                model_list = [best_current_model, eval_best_model]
            target_column_name = self.schema.target_column
            base_model_features_to_drop = self.schema.base_model_features_to_drop
            x_train = self.train_df.drop(base_model_features_to_drop, axis=1).values
            y_train = self.train_df[target_column_name].values
            x_test = self.test_df.drop(base_model_features_to_drop, axis=1).values
            y_test = self.test_df[target_column_name].values
    
            report_dir = self.model_pusher_config.report_dir
            base_accuracy = self.model_pusher_config.base_accuracy
            eval_difference = self.model_pusher_config.eval_difference
            eval_param = self.model_pusher_config.eval_param
            columns = list(self.schema.columns_to_eval)

            metric_report_artifact: MetricEvalArtifact = evaluate_classification_model(x_train_eval=x_train,
                                                                                    y_train=y_train,
                                                                                    x_test_eval=x_test,
                                                                                    y_test=y_test,
                                                                                    base_accuracy=base_accuracy,
                                                                                    report_dir=str(report_dir),
                                                                                    eval_difference=eval_difference,
                                                                                    estimators=model_list,
                                                                                    eval_param=eval_param,
                                                                                    experiment_id="model_eval",
                                                                                    columns=columns, final_eval=True)
            best_eval_model = metric_report_artifact.best_model
            if metric_report_artifact.best_model is None:
                response = ModelPusherArtifact(is_model_accepted=False,
                                                evaluated_model_path=best_model_path_reference)
                logger.info(response)
                return response

            else:
                logger.info("Trained model is found")
                eval_model_dir = self.model_pusher_config.report_dir
                eval_report_obj = metric_report_artifact.best_model_report
                eval_report_obj.save_html(os.path.join(eval_model_dir, "model_eval_report.html"))
                config_file_path = self.model_pusher_config.pipeline_config_file_path
                is_model_accepted = self.get_updated_model_status(report_obj=eval_report_obj,
                                                                config_file_path=config_file_path,
                                                                eval_model_dir=Path(eval_model_dir))
                PRODUCTION_MODEL_PATH = self.model_pusher_config.production_model_path
                if is_model_accepted:
                    logger.info("best Model accepted")
                    save_object(obj=best_eval_model, file_path=Path(best_model_path_reference))
                    save_object(obj=best_eval_model, file_path=Path(PRODUCTION_MODEL_PATH))
                    response = ModelPusherArtifact(best_model_path=best_model_path_reference,
                                                is_accepted=True)
                    return response
                else:
                    logger.warning("best Model already in production")
                    response = ModelPusherArtifact(best_model_path=PRODUCTION_MODEL_PATH,
                                                is_accepted=False)
                    return response

        except Exception as e:
            raise AppException(e, sys) from e

    def __del__(self):
        logger.info(f"{'>>' * 20}Model Pusher log completed.{'<<' * 20} ")


if __name__ == "__main__":
    
    args_parser = argparse.ArgumentParser()
    args_parser.add_argument('--config', dest='config', required=True)
    args_parser.add_argument('--model_config', dest='model_config', required=True)
    args_parser.add_argument('--feature_store', dest='feature_store', required=True)
    args_parser.add_argument('--schema_file', dest='schema', required=True)
    args = args_parser.parse_args()
    config = ConfigurationManager(config_file_path=args.config)
    data_ingestion_config = config.get_data_ingestion_config()
    data_validation_config = config.get_data_validation_config(schema_file_path=args.schema , data_ingestion_config=data_ingestion_config)
    data_transformation_config = config.get_data_transformation_config(
        feature_generator_config_file_path=args.feature_store, schema_file_path=args.schema , data_validation_config_info=data_validation_config)

    model_trainer_config = config.get_model_trainer_config(model_config_file_path=args.model_config,
                                                           schema_file_path=args.schema , data_transformation_config_info=data_transformation_config, 
                                                           data_validation_config_info= data_validation_config)
    model_eval_config_info = config.get_model_evaluation_config(schema_file_path=Path(args.schema), model_config_file_path=Path(args.model_config),
                                                                pipeline_config_file_path=Path(args.config) , data_validation_config_info=data_validation_config,
                                                                model_train_config=model_trainer_config)
    model_pusher_config_info = config.get_model_pusher_config( schema_file_path=Path(args.schema), model_config_file_path=Path(args.model_config),
                                                                pipeline_config_file_path=Path(args.config) , data_validation_config_info=data_validation_config,
                                                                model_eval_config=model_eval_config_info)
    model_pusher = ModelPusher(model_pusher_config=model_pusher_config_info)
    model_eval_response = model_pusher.initiate_model_pusher()