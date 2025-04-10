from utils.spark_utils import SparkUtils, ProcessData
import logging

# Create Spark Session
def main():
    app_name = 'nba_raw_to_silver_processor'
    config_file = {
        'spark_options': {
            'source': {
                'format': 'csv',
                'options':{
                    'header': 'true',
                    'delimiter': ',',
                    'inferSchema': 'true'
                },
                'process_type': 'file',
                'path':'s3a://datalake-landing/datalake-raw-nba/nba'
            },
            'target': {
                'format': 'delta',
                'options':{
                    'checkpoint': 's3a://datalake-bronze/datalake-bronze-nba/_checkpoints'
                },
                'path':'s3a://datalake-bronze/datalake-bronze-nba/nba',
                'mode': 'append'
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