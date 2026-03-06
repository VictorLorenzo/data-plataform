import logging

from data_framework.src.process import FileProcessor, SQLProcessor
from data_framework.src.settings import GoldSettings, SilverSettings
from utils.spark_session import get_spark_session  # noqa: F401 — re-exported for backward compat

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def execute_silver_settings_step(spark, silver_settings, step_settings):
    logger.info(f"Running {step_settings} for table {silver_settings['table']}")
    settings_instance = SilverSettings(settings=silver_settings)
    settings_rendered = settings_instance.get_rendered_config()[step_settings]
    logger.info(f"Rendered Settings: {settings_rendered}")
    processor = FileProcessor(spark, settings_rendered)
    processor.execute()


def execute_gold_settings_step(spark, gold_settings, step_settings):
    logger.info(f"Running {step_settings} for table {gold_settings['table']}")
    settings_instance = GoldSettings(settings=gold_settings)
    settings_rendered = settings_instance.get_rendered_config()[step_settings]
    logger.info(f"Rendered Settings: {settings_rendered}")
    processor = SQLProcessor(spark, settings_rendered)
    processor.execute()
