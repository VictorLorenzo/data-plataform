from utils.spark_utils import SparkUtils, ProcessData
import logging

# Create Spark Session
def main():
    app_name = "nba_raw_to_silver_processor"
    config_file = {
        "options": {
            "source": {
                "spark_options":{
                    "header": "true",
                    "delimiter": ",",
                    "inferSchema": "true"
                },
                "process_type": "file",
                "format": "csv",
                "spark_options":"",
                "path":"s3a://datalake-landing/datalake-raw-nba/nba"
            }
            
        }
    }
    spark_utils = SparkUtils()
    spark = spark_utils.get_spark_session(app_name)
    
    process_data = ProcessData(spark=spark, process_config = config_file)
    process_data.execute()

    spark.stop()

if __name__ == "__main__":
    main()