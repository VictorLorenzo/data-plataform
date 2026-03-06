from pyspark.sql import SparkSession
import logging
import os
import uuid

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def get_spark_session(app_name):
    """Create a SparkSession with embedded Hive metastore (Derby) configured.

    Each call sets up a unique Derby directory to avoid file-lock conflicts
    when multiple Airflow tasks run concurrently.

    CRITICAL DESIGN NOTES:

    1. javax.jdo.option.ConnectionURL uses an ABSOLUTE path to the Derby database.
       derby.system.home via System.setProperty is unreliable (Derby reads it once
       at boot). The absolute path in the URL bypasses derby.system.home entirely.

    2. spark.hadoop.javax.jdo.option.ConnectionURL does NOT work — DataNucleus
       sees the key WITH the "spark.hadoop." prefix and ignores it. The ConnectionURL
       must be set via System.setProperty (which HiveConf reads for this specific key).

    3. HMS initialization is LAZY — it only connects to Derby on the first
       spark_catalog operation. "SHOW DATABASES" goes to the default UC catalog
       and does NOT trigger HMS. We must force a spark_catalog operation
       (SHOW DATABASES IN spark_catalog) to trigger HMS, THEN create txn tables.

    4. The TxnHandler tables (NEXT_LOCK_ID, HIVE_LOCKS, etc.) are NOT managed by
       DataNucleus JDO — they must be created programmatically via JDBC after HMS
       has initialized the Derby database with autoCreateAll=true.
    """
    logger.info("Creating Spark Session")

    derby_dir = f"/tmp/derby_{uuid.uuid4().hex}"
    os.makedirs(derby_dir, exist_ok=True)
    db_path = os.path.join(derby_dir, "metastore_db")
    conn_url = f"jdbc:derby:{db_path};create=true"

    logger.info(f"Derby connection URL (absolute): {conn_url}")

    # Set javax.jdo.option.ConnectionURL as JVM System property BEFORE SparkSession.
    # HiveConf reads this specific key from System properties as a fallback.
    _set_derby_system_properties(derby_dir, conn_url)

    spark = (
        SparkSession
        .builder
        .appName(app_name)
        .config("spark.sql.catalogImplementation", "hive")
        .getOrCreate()
    )

    # Force the embedded HMS to actually initialize by touching spark_catalog.
    # SHOW DATABASES without specifying catalog goes to the default UC catalog
    # and does NOT trigger HMS. We must explicitly query spark_catalog.
    spark.sql("SHOW DATABASES IN spark_catalog").collect()
    logger.info("Embedded HMS initialized via spark_catalog query")

    # Verify the database was created where we expect
    if os.path.isdir(db_path):
        logger.info(f"Confirmed: Derby database exists at {db_path}")
    else:
        logger.warning(f"Derby database NOT found at {db_path}! "
                       f"Contents of {derby_dir}: {os.listdir(derby_dir)}")

    # Create Hive transaction tables that DataNucleus can't auto-create.
    # Must happen AFTER HMS has initialized Derby (i.e., after spark_catalog query).
    _create_hive_txn_tables(spark, db_path)

    logger.info(f"Embedded HMS Derby database configured at: {db_path}")
    return spark


def _set_derby_system_properties(derby_dir, conn_url):
    """Set JVM system properties for Derby BEFORE SparkSession creation.

    Uses SparkContext._gateway to access the JVM before SparkSession exists,
    since spark-submit has already started the JVM by the time Python runs.

    HiveConf reads javax.jdo.option.ConnectionURL from System properties as
    a fallback when not found in hive-site.xml. Since we removed the static
    ConnectionURL from hive-site.xml, this System property is the primary source.
    """
    from pyspark import SparkContext
    SparkContext._ensure_initialized()
    jvm = SparkContext._gateway.jvm

    jvm.System.setProperty("derby.system.home", derby_dir)
    jvm.System.setProperty("javax.jdo.option.ConnectionURL", conn_url)

    logger.info(f"Derby system properties set: derby.system.home={derby_dir}")


def _create_hive_txn_tables(spark, db_path):
    """Create Hive transaction schema tables in Derby that DataNucleus can't auto-create.

    The TxnHandler requires TXNS, NEXT_LOCK_ID, HIVE_LOCKS, and related tables.
    These are part of the Hive metastore schema init SQL and are NOT managed by
    DataNucleus JDO, so autoCreateAll=true does not create them.

    Uses py4j JDBC with the ABSOLUTE path to the Derby database.
    """
    jvm = spark._jvm

    conn_url = f"jdbc:derby:{db_path}"
    logger.info(f"Creating txn tables via JDBC: {conn_url}")

    try:
        jvm.Class.forName("org.apache.derby.jdbc.EmbeddedDriver")
        conn = jvm.java.sql.DriverManager.getConnection(conn_url)
    except Exception as e:
        logger.error(f"Failed to connect to Derby at {conn_url}: {e}")
        parent = os.path.dirname(db_path)
        if os.path.isdir(parent):
            logger.error(f"Contents of {parent}: {os.listdir(parent)}")
        return

    try:
        stmt = conn.createStatement()
        for ddl in _get_txn_ddl():
            try:
                stmt.execute(ddl)
            except Exception as e:
                if "already exists" not in str(e).lower():
                    logger.warning(f"DDL warning: {e}")
        conn.commit()
        logger.info("Hive transaction schema tables created successfully.")
    finally:
        try:
            stmt.close()
        except Exception:
            pass


def _get_txn_ddl():
    """Return the full Hive 2.3.0 transaction schema DDL for Derby.

    Copied from hive-txn-schema-2.3.0.derby.sql (rel/release-2.3.9).
    All columns must match exactly — TxnHandler SELECTs/INSERTs by column name.
    """
    return [
        """CREATE TABLE TXNS (
            TXN_ID bigint PRIMARY KEY,
            TXN_STATE char(1) NOT NULL,
            TXN_STARTED bigint NOT NULL,
            TXN_LAST_HEARTBEAT bigint NOT NULL,
            TXN_USER varchar(128) NOT NULL,
            TXN_HOST varchar(128) NOT NULL,
            TXN_AGENT_INFO varchar(128),
            TXN_META_INFO varchar(128),
            TXN_HEARTBEAT_COUNT integer
        )""",
        "CREATE TABLE NEXT_TXN_ID (NTXN_NEXT bigint NOT NULL)",
        "INSERT INTO NEXT_TXN_ID VALUES(1)",
        "CREATE TABLE NEXT_LOCK_ID (NL_NEXT bigint NOT NULL)",
        "INSERT INTO NEXT_LOCK_ID VALUES(1)",
        "CREATE TABLE NEXT_COMPACTION_QUEUE_ID (NCQ_NEXT bigint NOT NULL)",
        "INSERT INTO NEXT_COMPACTION_QUEUE_ID VALUES(1)",
        """CREATE TABLE TXN_COMPONENTS (
            TC_TXNID bigint NOT NULL REFERENCES TXNS (TXN_ID),
            TC_DATABASE varchar(128) NOT NULL,
            TC_TABLE varchar(128),
            TC_PARTITION varchar(767),
            TC_OPERATION_TYPE char(1) NOT NULL
        )""",
        """CREATE TABLE COMPLETED_TXN_COMPONENTS (
            CTC_TXNID bigint NOT NULL,
            CTC_DATABASE varchar(128) NOT NULL,
            CTC_TABLE varchar(256),
            CTC_PARTITION varchar(767)
        )""",
        """CREATE TABLE HIVE_LOCKS (
            HL_LOCK_EXT_ID bigint NOT NULL,
            HL_LOCK_INT_ID bigint NOT NULL,
            HL_TXNID bigint,
            HL_DB varchar(128) NOT NULL,
            HL_TABLE varchar(128),
            HL_PARTITION varchar(767),
            HL_LOCK_STATE char(1) NOT NULL,
            HL_LOCK_TYPE char(1) NOT NULL,
            HL_LAST_HEARTBEAT bigint NOT NULL,
            HL_ACQUIRED_AT bigint,
            HL_USER varchar(128) NOT NULL,
            HL_HOST varchar(128) NOT NULL,
            HL_HEARTBEAT_COUNT integer,
            HL_AGENT_INFO varchar(128),
            HL_BLOCKEDBY_EXT_ID bigint,
            HL_BLOCKEDBY_INT_ID bigint,
            PRIMARY KEY(HL_LOCK_EXT_ID, HL_LOCK_INT_ID)
        )""",
        "CREATE INDEX HL_TXNID_INDEX ON HIVE_LOCKS (HL_TXNID)",
        """CREATE TABLE COMPACTION_QUEUE (
            CQ_ID bigint PRIMARY KEY,
            CQ_DATABASE varchar(128) NOT NULL,
            CQ_TABLE varchar(128) NOT NULL,
            CQ_PARTITION varchar(767),
            CQ_STATE char(1) NOT NULL,
            CQ_TYPE char(1) NOT NULL,
            CQ_TBLPROPERTIES varchar(2048),
            CQ_WORKER_ID varchar(128),
            CQ_START bigint,
            CQ_RUN_AS varchar(128),
            CQ_HIGHEST_TXN_ID bigint,
            CQ_META_INFO varchar(2048) FOR BIT DATA,
            CQ_HADOOP_JOB_ID varchar(32)
        )""",
        """CREATE TABLE COMPLETED_COMPACTIONS (
            CC_ID bigint PRIMARY KEY,
            CC_DATABASE varchar(128) NOT NULL,
            CC_TABLE varchar(128) NOT NULL,
            CC_PARTITION varchar(767),
            CC_STATE char(1) NOT NULL,
            CC_TYPE char(1) NOT NULL,
            CC_TBLPROPERTIES varchar(2048),
            CC_WORKER_ID varchar(128),
            CC_START bigint,
            CC_END bigint,
            CC_RUN_AS varchar(128),
            CC_HIGHEST_TXN_ID bigint,
            CC_META_INFO varchar(2048) FOR BIT DATA,
            CC_HADOOP_JOB_ID varchar(32)
        )""",
        """CREATE TABLE AUX_TABLE (
            MT_KEY1 varchar(128) NOT NULL,
            MT_KEY2 bigint NOT NULL,
            MT_COMMENT varchar(255),
            PRIMARY KEY(MT_KEY1, MT_KEY2)
        )""",
        """CREATE TABLE WRITE_SET (
            WS_DATABASE varchar(128) NOT NULL,
            WS_TABLE varchar(128) NOT NULL,
            WS_PARTITION varchar(767),
            WS_TXNID bigint NOT NULL,
            WS_COMMIT_ID bigint NOT NULL,
            WS_OPERATION_TYPE char(1) NOT NULL
        )""",
    ]
