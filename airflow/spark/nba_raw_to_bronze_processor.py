from utils.spark_utils import SparkUtils, ProcessData
import logging

# Create Spark Session
def main():
    app_name = "nba_raw_to_silver_processor"
    config_file = {
        "type_processing": "batch",
        "spark_options": {
            "source": {
                "format": "csv",
                "options":{
                    "header": "true",
                    "delimiter": ",",
                    "inferSchema": "true"
                },
                "process_type": "file",
                "path":"s3a://datalake-landing/datalake-raw-nba/nba"
            },
            "target": {
                "database": "nba_bronze",
                "table": "nba",
                "format": "delta",
                "options":{
                    "checkpoint": "s3a://datalake-bronze/datalake-bronze-nba/_checkpoints",
                    "output_mode": "append",
                    "apply_as_delete": None
                },
                "path":"s3a://datalake-bronze/datalake-bronze-nba/nba",
                "primary_key": ["PLAYER_ID", "SECS_LEFT", "MINS_LEFT", "GAME_ID"],
                "sequence_by": ["_bronze_created_at"],
                "sql_transform":{
                    "10-add-layser-columns": ["input_file_name() _filename", "current_timestamp() _bronze_created_at"],
                },
                "drop_columns": []
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