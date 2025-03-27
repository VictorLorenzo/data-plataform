from utils.spark_utils import SparkUtils, ProcessData

# Create Spark Session
def main():
    app_name = "nba_raw_to_silver_processor"
    spark_utils = SparkUtils()
    spark = spark_utils.get_spark_session(app_name)

