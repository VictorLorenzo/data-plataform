from utils.processing_utils import get_spark_session, execute_gold_settings_step
from utils.common_utils import read_json_file
import sys

def main(gold_settings_file, step_settings):
    gold_settings = read_json_file(gold_settings_file)
    app_name = f'Job for table {gold_settings["table"]}, step {step_settings}'

    spark = get_spark_session(app_name)
    execute_gold_settings_step(spark, gold_settings, step_settings)
    spark.stop()

if __name__ == "__main__":
    gold_settings_file = sys.argv[1]
    step_settings = sys.argv[2]
    main(gold_settings_file, step_settings)
