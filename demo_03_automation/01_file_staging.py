# Databricks notebook source
# MAGIC %md
# MAGIC # UC3a · File staging — pick the right version by name, stage it, log it
# MAGIC
# MAGIC The report-staging job: report files land in **two folders** on a schedule; at the start of the
# MAGIC month you find, **for each report code, the correct version *by the date-time stamp in the file
# MAGIC name*** (not the latest-*arrived* — a file stamped the 2nd beats one arriving later stamped the 1st),
# MAGIC and **copy** the chosen files to a destination folder. No data is changed — it's pure file movement.
# MAGIC
# MAGIC Honest framing: this isn't a **Designer** transform — it's file/OS logic, so it belongs in a
# MAGIC **Lakeflow Job** with **Autoloader**. The platform gives the schedule, the autonomous run
# MAGIC (fires when files land — no one clicks *Run*), and the audit trail for free.
# MAGIC
# MAGIC Everything synthetic, prefixed `af_`.

# COMMAND ----------

dbutils.widgets.text("catalog_name", "lr_dev_aws_us_catalog")
dbutils.widgets.text("schema_name", "designer_recon_demo")
dbutils.widgets.text("landing_volume_name", "recon_landing")
catalog = dbutils.widgets.get("catalog_name")
schema = dbutils.widgets.get("schema_name")
volume = dbutils.widgets.get("landing_volume_name")
fqn = f"{catalog}.{schema}"
spark.sql(f"CREATE SCHEMA IF NOT EXISTS {fqn}")
spark.sql(f"CREATE VOLUME IF NOT EXISTS {fqn}.{volume}")

vroot = f"/Volumes/{catalog}/{schema}/{volume}/uc3a"
sources = f"{vroot}/sources"
dest = f"{vroot}/destination"
schema_loc = f"{vroot}/_schema"
checkpoint = f"{vroot}/_checkpoint"

# COMMAND ----------

# MAGIC %md
# MAGIC ## Land versioned files in two folders (report code + version + date in the name)

# COMMAND ----------

# reset for idempotent re-runs
dbutils.fs.rm(vroot, True)
for d in [f"{sources}/folder_a", f"{sources}/folder_b", dest]:
    dbutils.fs.mkdirs(d)

# report files: identity is entirely in the NAME (report code + descriptor + date-time stamp); content is
# opaque — we only move the file. Some report codes arrive twice; the LATER stamp is the correct version.
layout = {"folder_a": [("RPT02", "Claims_Suspense"), ("RPT03", "Claims_Ignored")],
          "folder_b": [("RPT61", "Fleet_Motor_Claims"), ("RPT77", "Household_Suspense")]}
stamps = {"RPT02": ["2026-09-01-07-30-38", "2026-09-02-07-30-22"],   # two versions -> later chosen
          "RPT03": ["2026-09-02-07-32-36"],
          "RPT61": ["2026-08-31-07-42-52", "2026-09-01-07-40-10"],   # two versions -> later chosen
          "RPT77": ["2026-09-02-07-45-01"]}
landed = []
for folder, codes in layout.items():
    for code, desc in codes:
        for ts in stamps[code]:
            name = f"{code}_{desc}_TEXT_{ts}.txt"
            dbutils.fs.put(f"{sources}/{folder}/{name}", "dummy\n", True)   # opaque content — pure file movement
            landed.append(f"{folder}/{name}")
print(f"landed {len(landed)} files across two folders:")
for f in sorted(landed): print("  ", f)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Autoloader sees every file that lands (incremental, fires on arrival)

# COMMAND ----------

spark.sql(f"DROP TABLE IF EXISTS {fqn}.af_files_bronze")
(spark.readStream.format("cloudFiles")
    .option("cloudFiles.format", "binaryFile")
    .option("cloudFiles.schemaLocation", schema_loc)
    .load(sources)
    .selectExpr("path", "length", "modificationTime")
    .writeStream.option("checkpointLocation", checkpoint)
    .trigger(availableNow=True)
    .toTable(f"{fqn}.af_files_bronze")).awaitTermination()

# COMMAND ----------

# MAGIC %md
# MAGIC ## Account for EVERY file: chosen (highest version) / superseded / unrecognized

# COMMAND ----------

# every file gets a disposition — nothing is silently ignored or mis-staged
spark.sql(f"""
CREATE OR REPLACE TABLE {fqn}.af_version_audit AS
WITH parsed AS (
  SELECT path,
         element_at(split(path, '/'), -1)                                       AS file_name,
         element_at(split(path, '/'), -2)                                       AS folder,
         regexp_extract(element_at(split(path,'/'),-1), '^(RPT\\\\d+)_', 1)        AS report_code,
         regexp_extract(element_at(split(path,'/'),-1), '_TEXT_(.+)\\\\.txt', 1)   AS name_stamp
  FROM {fqn}.af_files_bronze)
SELECT folder, report_code, name_stamp AS version, file_name, path,
       CASE WHEN report_code = '' OR name_stamp = '' THEN 'unrecognized'
            WHEN name_stamp = max(name_stamp) OVER (PARTITION BY folder, report_code) THEN 'chosen'
            ELSE 'superseded' END                                               AS disposition
FROM parsed
""")
spark.sql(f"COMMENT ON TABLE {fqn}.af_version_audit IS 'UC3a every file seen + disposition (chosen/superseded/unrecognized). Synthetic.'")
spark.sql(f"CREATE OR REPLACE TABLE {fqn}.af_files_staged AS SELECT folder, report_code, version, file_name, path FROM {fqn}.af_version_audit WHERE disposition = 'chosen'")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Copy the chosen files, log the run, and reconcile (seen = chosen + superseded + unrecognized)

# COMMAND ----------

staged = spark.table(f"{fqn}.af_files_staged").collect()
copied = 0
for r in staged:
    dbutils.fs.cp(r["path"], f"{dest}/{r['file_name']}")
    copied += 1

d = {row["disposition"]: row["n"] for row in spark.sql(
    f"SELECT disposition, count(*) n FROM {fqn}.af_version_audit GROUP BY disposition").collect()}
seen = spark.table(f"{fqn}.af_files_bronze").count()
chosen, superseded, unrecognized = d.get("chosen", 0), d.get("superseded", 0), d.get("unrecognized", 0)
assert chosen + superseded + unrecognized == seen, "file-count reconciliation failed — a file is unaccounted for"

spark.sql(f"""CREATE TABLE IF NOT EXISTS {fqn}.af_staging_audit
  (run_ts TIMESTAMP, files_seen INT, chosen INT, superseded INT, unrecognized INT, files_copied INT)""")
spark.sql(f"""INSERT INTO {fqn}.af_staging_audit VALUES
  (current_timestamp(), {seen}, {chosen}, {superseded}, {unrecognized}, {copied})""")

print(f"seen {seen} = chosen {chosen} + superseded {superseded} + unrecognized {unrecognized}  ·  copied {copied}")
print("Destination now holds:", [f.name for f in dbutils.fs.ls(dest)])
display(spark.sql(f"SELECT folder, report_code, version, disposition, file_name FROM {fqn}.af_version_audit ORDER BY folder, report_code, version DESC"))
print("Schedule as a Lakeflow Job (monthly) or let Autoloader fire on arrival. The version audit shows "
      "exactly which file was chosen and why the others weren't — no file silently ignored, none mis-picked.")
