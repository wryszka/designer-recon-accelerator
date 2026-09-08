# Databricks notebook source
# MAGIC %md
# MAGIC # UC3a · File staging — Autoloader + audit log (the "scheduled automation" answer)
# MAGIC
# MAGIC The finance team's question: *"a small Python script scans folders, picks the earliest
# MAGIC version of each report for a period and stages it. Can the platform run that on a
# MAGIC schedule, autonomously, with an audit trail — comparable to what we'd build ourselves?"*
# MAGIC
# MAGIC Answer, and the honest framing: this isn't a Lakeflow **Designer** job (it's file/OS
# MAGIC logic, not a visual transform) — it belongs in a **Lakeflow Job** with **Autoloader**.
# MAGIC The platform gives you the scheduling, the autonomous run and the audit log for free:
# MAGIC Autoloader ingests only new files incrementally; a run-log table + the Job run history
# MAGIC and Unity Catalog audit give you the compliance trail.
# MAGIC
# MAGIC Everything synthetic, prefixed `af_`. No real report or system.

# COMMAND ----------

dbutils.widgets.text("catalog_name", "lr_dev_aws_us_catalog")
dbutils.widgets.text("schema_name", "designer_recon_demo")
dbutils.widgets.text("landing_volume_name", "recon_landing")
dbutils.widgets.text("period", "2026-09")
catalog = dbutils.widgets.get("catalog_name")
schema = dbutils.widgets.get("schema_name")
volume = dbutils.widgets.get("landing_volume_name")
period = dbutils.widgets.get("period")
fqn = f"{catalog}.{schema}"
spark.sql(f"CREATE SCHEMA IF NOT EXISTS {fqn}")
spark.sql(f"CREATE VOLUME IF NOT EXISTS {fqn}.{volume}")
incoming = f"/Volumes/{catalog}/{schema}/{volume}/reports_incoming"
schema_loc = f"/Volumes/{catalog}/{schema}/{volume}/_af_schema"
checkpoint = f"/Volumes/{catalog}/{schema}/{volume}/_af_checkpoint"

# COMMAND ----------

# MAGIC %md
# MAGIC ## Drop versioned report files into the folder (two report codes, two versions each)

# COMMAND ----------

dbutils.fs.mkdirs(incoming)
for f in dbutils.fs.ls(incoming):
    dbutils.fs.rm(f.path)
dbutils.fs.rm(schema_loc, True); dbutils.fs.rm(checkpoint, True)
spark.sql(f"DROP TABLE IF EXISTS {fqn}.af_files_bronze")

# RPT02 and RPT07, each with an earlier and a later timestamped version for the period
for code in ["RPT02", "RPT07"]:
    for ts in ["00-44-05", "06-12-30"]:
        p = f"{incoming}/{code}_claims_suspense_{period}-01-{ts}.txt"
        dbutils.fs.put(p, f"report {code} period {period} generated {ts}\nrun-number,txn-type,count,amount\n1,MOTOR,10,12345.67\n", True)
print("landed:", [f.name for f in dbutils.fs.ls(incoming)])

# COMMAND ----------

# MAGIC %md
# MAGIC ## Autoloader ingests the folder incrementally (binary → file metadata)

# COMMAND ----------

(spark.readStream.format("cloudFiles")
    .option("cloudFiles.format", "binaryFile")
    .option("cloudFiles.schemaLocation", schema_loc)
    .load(incoming)
    .selectExpr("path", "length", "modificationTime")
    .writeStream.option("checkpointLocation", checkpoint)
    .trigger(availableNow=True)
    .toTable(f"{fqn}.af_files_bronze")).awaitTermination()

# COMMAND ----------

# MAGIC %md
# MAGIC ## Stage the EARLIEST version of each report code for the period

# COMMAND ----------

spark.sql(f"""
CREATE OR REPLACE TABLE {fqn}.af_files_staged AS
WITH parsed AS (
  SELECT path, length, modificationTime,
         regexp_extract(path, '(RPT\\\\d+)_', 1)                 AS report_code,
         regexp_extract(path, '_(\\\\d{{4}}-\\\\d{{2}})-',   1)  AS period,
         element_at(split(path, '/'), -1)                       AS file_name
  FROM {fqn}.af_files_bronze)
SELECT * FROM (
  SELECT *, row_number() OVER (PARTITION BY report_code, period ORDER BY file_name ASC) AS rn
  FROM parsed)
WHERE rn = 1
""")

# audit log — one row per run, for the compliance trail
spark.sql(f"CREATE TABLE IF NOT EXISTS {fqn}.af_staging_audit (run_ts TIMESTAMP, period STRING, files_seen INT, files_staged INT)")
spark.sql(f"""INSERT INTO {fqn}.af_staging_audit
  SELECT current_timestamp(), '{period}',
         (SELECT count(*) FROM {fqn}.af_files_bronze),
         (SELECT count(*) FROM {fqn}.af_files_staged)""")

print("bronze files:", spark.table(f"{fqn}.af_files_bronze").count(),
      "· staged (earliest per code):", spark.table(f"{fqn}.af_files_staged").count())
display(spark.sql(f"SELECT report_code, period, file_name FROM {fqn}.af_files_staged ORDER BY report_code"))
display(spark.sql(f"SELECT * FROM {fqn}.af_staging_audit ORDER BY run_ts DESC"))
print("Schedule this notebook as a Lakeflow Job (e.g. monthly). Every run appends to "
      "af_staging_audit; the Job run history + Unity Catalog system.access.audit give the full trail.")
