from delta.tables import DeltaTable
from pyspark.sql import SparkSession
from pyspark.sql.functions import col


def merge_delta(delta_table, new_data, merge_key):
    (
        delta_table.alias("old_data")
            .merge(
                new_data.alias("new_data"),
                f"old_data.{merge_key} = new_data.{merge_key}"
            )
            .whenMatchedUpdate(set = {
                "name": col("new_data.name")
            })
            .whenNotMatchedInsert(values = {
                "name": col("new_data.name")
            })
            .execute()
    )

    return delta_table


def create_delta(new_data, delta_path, schema, table):
    (
        new_data.write.format("delta")
            .option("delta.columnMapping.mode", "name")
            .option("path", delta_path)
            .saveAsTable(f"{schema}.{table}")
    )


def main():
    source_bucket = "datalake-landing/datalake-raw-nba/nba"
    target_bucket = "datalake"
    schema = "datalake"
    table = "nba"
    primary_key = "name"

    spark = SparkSession.builder \
        .appName("CSV File to Delta Lake Table") \
        .enableHiveSupport() \
        .getOrCreate()

    input_path = f"s3a://{source_bucket}/*.csv"
    #delta_path = f"s3a://{target_bucket}/delta/datalake/tables/{table}"

    new_data = spark.read.csv(input_path, header=True, inferSchema=True)
    new_data.show(10)
#
    #spark.sql(f"CREATE DATABASE IF NOT EXISTS {schema}")
    #spark.sql(f"USE {schema}")
#
    #try:
    #    delta_table = DeltaTable.forPath(spark, delta_path)
    #    delta_table = merge_delta(delta_table, new_data, primary_key)
    #except:
    #    create_delta(new_data, delta_path, schema, table)
    #    delta_table = DeltaTable.forName(spark, f"{schema}.{table}")
#
    #delta_table.toDF().show(10)


if __name__ == "__main__":
    main()