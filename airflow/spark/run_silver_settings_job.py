from utils.processing_utils import get_spark_session, execute_silver_settings_step
from utils.common_utils import read_json_file
import sys

def main(silver_settings_file, step_settings):
    silver_settings = read_json_file(silver_settings_file)
    app_name = f'Job for table {silver_settings["table"]}, step {step_settings}'

    spark = get_spark_session(app_name)
    execute_silver_settings_step(spark, silver_settings, step_settings)
    spark.stop()

if __name__ == "__main__":
    silver_settings_file = sys.argv[1]
    step_settings = sys.argv[2]
    main(silver_settings_file, step_settings)
