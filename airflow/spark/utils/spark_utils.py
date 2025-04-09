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

    def _build_writer(self, df):
        process_config = self.process_config

    def execute(self):
        logger = self.logger
        process_config = self.process_config

        try:
            if process_config["options"]["process_type"] == "file":
                self.process_file()

            self.process_sql()

        except Exception as e:
            logger.error("An error ocurred: %s", str(e))
            logger.info("Data processing finished with errors.")
            raise e

    def _read_source_file(self):
        spark = self.spark
        process_config = self.process_config

        if process_config["options"]["format"] != "delta":
            static_df = (spark
                    .read
                    .format(process_config["options"]["format"])
                    .option(**process_config["options"]["spark_options"])
                    .load(process_config["options"]["path"])
            )
            schema = static_df.schema

            df = (
                spark.readStream
                    .format(process_config["options"]["format"])
                    .option(**process_config["options"]["spark_options"])
                    .schema(schema)
                    .load(process_config["options"]["path"])
            )
        else:
            df = (
                spark.readStream
                    .format(process_config["options"]["source"]["format"])
                    .load(process_config["options"]["source"]["path"])
            )

        return df
