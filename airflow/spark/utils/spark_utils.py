import random
from pyspark.sql import SparkSession
from delta.tables import DeltaTable

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

    def process_file(self):
        df = self._read_source_file()
        writer = self._build_writer(df)
        self.execute_process_streaming(writer)

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

    def _build_writer(self, df):
        process_config = self.process_config
        type_processing = process_config["type_processing"]

        if df.isStreaming:
            writer = (
                df.writeStream
                .format(process_config["spark_options"]["target"]["format"])
                .option("path", process_config["spark_options"]["target"]["path"])
                .option("checkpointLocation", process_config["spark_options"]["target"]["options"]["checkpoint"])
                .outputMode(process_config["spark_options"]["target"]["options"]["output_mode"])
                .foreachBatch(self._foreach_batch)
                .queryName(f"writing_{type_processing}_{process_config['spark_options']['target']['table']}")
            )

            return writer

    def _foreach_batch(self, df, batch_id):
        logger = self.logger

        logger.info(f"Batch ID: {batch_id}")

        source = "source_"
        target = "target_"

        self._create_database()

        df = self._add_collums(df)

        df = self._drop_columns(df)

        table = self._create_table(df.schema)

        self.merge_data(table, df, source, target)

    def merge_data(self, table, df, source, target):
        logger = self.logger
        process_config = self.process_config
        primary_key = process_config["spark_options"]["target"]["primary_key"]   
        merge_condition = "\n AND ".join([f"{source}.{key} = {target}.{key}" for key in primary_key]) if primary_key else "1 = 0"
        sequence_by = process_config["spark_options"]["target"]["sequence_by"]
        sequence_by_condition = "\n AND ".join([f"{source}.{key} >= {target}.{key}" for key in sequence_by]) if sequence_by else "1 = 0"
        appply_as_delete = process_config["spark_options"]["target"]["options"]["apply_as_delete"]

        logger.info("Delta table merge started.")

        logger.info(f"""   
                    MERGE INTO {table} AS {target}
                    USING {df} AS {source}
                    ON {merge_condition}
                    WHEN MATCHED AND {sequence_by_condition} THEN
                        UPDATE SET *
                    WHEN NOT MATCHED THEN  
                    """)
        print("sequence by condition: ",sequence_by_condition)
        try:
            merge = (
                table.alias(target)
                .merge(
                    df.alias(source),
                    merge_condition
                )
            )

            if sequence_by:
                merge = merge.whenMatchedUpdateAll(
                    condition=sequence_by_condition)
            
            else:
                merge = merge.whenMatchedUpdateAll()

            if appply_as_delete:
                merge = merge.whenMatchedDelete(
                    condition=appply_as_delete
                )

            merge = merge.whenNotMatchedInsertAll()
            merge.execute()
            logger.info("Delta table merge completed successfully.")
        except Exception as e:
            logger.error(f"Error during Delta table merge: {str(e)}")
            raise e

    def _create_table(self, schema):
        spark = self.spark
        logger = self.logger
        process_config = self.process_config
        db_name = process_config["spark_options"]["target"]["database"]
        table_name = process_config["spark_options"]["target"]["table"]
        table_path = process_config["spark_options"]["target"]["path"]
        table_full_name = f"{db_name}.{table_name}"

        try:
            if not DeltaTable.isDeltaTable(spark, table_full_name):
                delta_table_build = (
                    DeltaTable.createIfNotExists(spark)
                    .tableName(table_full_name)
                    .location(table_path)
                    .comment("Table created by Delta Lake")
                    .addColumns(schema)
                )
                delta_table = delta_table_build.execute()
                logger.info(f"Table {table_full_name} created successfully.")
                return delta_table
            else:
                logger.info(f"Table {table_full_name} already exists.")
                return DeltaTable.forPath(spark, table_full_name, table_path)
        except Exception as e:
            logger.error(f"Error creating table {table_full_name}: {str(e)}")
            raise e

    def _drop_columns(self, df):
        logger = self.logger
        process_config = self.process_config
        drop_columns = process_config["spark_options"]["target"]["drop_columns"]

        if drop_columns:
            df = df.drop(*drop_columns)

        return df

    def _create_database(self):
        spark = self.spark
        logger = self.logger
        process_config = self.process_config
        db_name = process_config["spark_options"]["target"]["database"]
        db_path = process_config["spark_options"]["target"]["path"]

        try:
            spark.sql(f"CREATE DATABASE IF NOT EXISTS {db_name} LOCATION '{db_path}'")
            logger.info(f"Database {db_name} created successfully.")
        except Exception as e:
            logger.error(f"Error creating database {db_name}: {str(e)}")
            raise e

    def _add_collums(self, df):
        logger = self.logger
        process_config = self.process_config
        sql_transform = process_config["spark_options"]["target"]["sql_transform"]

        try:
            for column, value in sorted(sql_transform.items()):
                logger.info(f"Adding column {column} with value {value}")
                df = df.selectExpr("*", *value)
            logger.info("Columns added successfully.")
            return df
        except Exception as e:
            logger.error(f"Error adding columns: {str(e)}")
            raise e

    def execute_process_streaming(self,writer):
        typer_processing = self.process_config["type_processing"]
        if writer:
            if typer_processing == "streaming":
                writer = writer.trigger(processingTime="30 seconds")
            else:
                writer = writer.trigger(
                    availableNow=True
                )
            
            writer.start().awaitTermination()
