from pyspark.sql import SparkSession
import logging

from data_framework.src.process import FileProcessor, SQLProcessor
from data_framework.src.settings import GoldSettings, SilverSettings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Creat Spark Session
def get_spark_session(app_name):
    logger.info("Creating Spark Session")
    spark = (
        SparkSession
        .builder
        .appName(app_name)
        .enableHiveSupport()
        .getOrCreate()
    )

    return spark

# Execute step raw_to_bronze or bronze_to_silver for silver settings
def execute_silver_settings_step(spark, silver_settings, step_settings):
    logger.info(f"Running {step_settings} for table {silver_settings['table']}")
    settings_instance = SilverSettings(settings=silver_settings)
    settings_rendered = settings_instance.get_rendered_config()[step_settings]
    logger.info(f"Rendered Settings: {settings_rendered}")
    processor = FileProcessor(spark, settings_rendered)
    processor.execute()

# Execute step silver_to_gold for gold settings
def execute_gold_settings_step(spark, gold_settings, step_settings):
    logger.info(f"Running {step_settings} for table {gold_settings['table']}")
    settings_instance = GoldSettings(settings=gold_settings)
    settings_rendered = settings_instance.get_rendered_config()[step_settings]
    logger.info(f"Rendered Settings: {settings_rendered}")
    processor = SQLProcessor(spark, settings_rendered)
    processor.execute()
