import random
from pyspark.sql import SparkSession
import logging

class SparkUtils():
    def __init__(self):
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

    def get_spark_session(self,app_name):
        self.logger.info(app_name)
        spark = (
            SparkSession
            .builder
            .appName(app_name)
            .enableHiveSupport()
            .getOrCreate()
        )

        return spark

class ProcessData():
    def __init__(self, spark, process_config):
        self.spark = spark
        self.process_config = process_config
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

    def process_file(self):
        df = self._read_source_file()
        writer = self._build_writer(df)
        #self.execute_process_streaming(writer)

    def _build_writer(self, df):
        process_config = self.process_config
        process_config = process_config["type_processing"]
        if df.isStreaming:
            writer = (
                df.writeStream
                .format(process_config["spark_options"]["target"]["format"])
                .option("path", process_config["spark_options"]["target"]["path"])
                .option("checkpointLocation", process_config["spark_options"]["target"]["options"]["checkpoint"])
                .outputMode(process_config["spark_options"]["target"]["options"]["output_mode"])
                .foreachBatch(self._foreach_batch)
                .queryName(f"writeing table into deltalake")
            )

    def _foreach_batch(self, df, batch_id):

    def execute_process_streaming(self,writer):
        writer = writer.trigger(
            availableNow=True
        )

        writer.start().awaitTermination()

    def execute(self):
        logger = self.logger
        process_config = self.process_config

        try:
            if process_config["spark_options"]["source"]["process_type"] == "file":
                self.process_file()

        except Exception as e:
            logger.error("An error ocurred: %s", str(e))
            logger.info("Data processing finished with errors.")
            raise e

    def _read_source_file(self):
        spark = self.spark
        process_config = self.process_config

        if process_config["spark_options"]["source"]["format"] != "delta":
            print(process_config["spark_options"]["source"]["options"])
            static_df = (
                spark.read
                    .format(process_config["spark_options"]["source"]["format"])
                    .options(**process_config["spark_options"]["source"]["options"])
                    .load(process_config["spark_options"]["source"]["path"])
            )
            schema = static_df.schema

            df = (
                spark.readStream
                    .format(process_config["spark_options"]["source"]["format"])
                    .options(**process_config["spark_options"]["source"]["options"])
                    .schema(schema)
                    .load(process_config["spark_options"]["source"]["path"])
            )
        else:
            df = (
                spark.readStream
                    .format(process_config["spark_options"]["source"]["source"]["format"])
                    .load(process_config["spark_options"]["source"]["source"]["path"])
            )

        return df
