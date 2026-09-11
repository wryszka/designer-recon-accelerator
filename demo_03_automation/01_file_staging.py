# Databricks notebook source
# MAGIC %md
# MAGIC # UC3a · File staging — pick the right version by name, stage it, log it
# MAGIC
# MAGIC The ACS Station-Journal job: files land in **two folders** on a schedule; at the start of the
# MAGIC month you find, **for each report code, the correct version *by file name*** (not the
# MAGIC latest-arrived — a v02 that arrived on the 28th is still preferred over a v01 that arrived on
# MAGIC the 29th), and **copy** the chosen files to a destination folder. No data is changed — it's
# MAGIC pure file movement.
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

import numpy as np
rng = np.random.default_rng(11)

# reset for idempotent re-runs
dbutils.fs.rm(vroot, True)
for d in [f"{sources}/folder_a", f"{sources}/folder_b", dest]:
    dbutils.fs.mkdirs(d)

layout = {"folder_a": ["0230", "0270", "0310"], "folder_b": ["0450", "0520"]}
landed = []
for folder, codes in layout.items():
    for code in codes:
        n_versions = int(rng.integers(1, 4))                 # 1–3 versions per code
        for v in range(1, n_versions + 1):
            date = f"202606{10 + v:02d}"                     # later version = later date in name
            name = f"ACS_{code}_v{v:02d}_{date}.csv"
            dbutils.fs.put(f"{sources}/{folder}/{name}",
                           f"station,journal,amount\nST{code},{date},{1000*v}\n", True)
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
# MAGIC ## Select the highest version per (folder, report code) — purely by file name

# COMMAND ----------

spark.sql(f"""
CREATE OR REPLACE TABLE {fqn}.af_files_staged AS
WITH parsed AS (
  SELECT path,
         element_at(split(path, '/'), -1)                          AS file_name,
         element_at(split(path, '/'), -2)                          AS folder,
         regexp_extract(path, 'ACS_(\\\\d+)_', 1)                    AS report_code,
         CAST(regexp_extract(path, '_v(\\\\d+)_', 1) AS INT)         AS version
  FROM {fqn}.af_files_bronze)
SELECT folder, report_code, version, file_name, path FROM (
  SELECT *, row_number() OVER (PARTITION BY folder, report_code ORDER BY version DESC) AS rn
  FROM parsed)
WHERE rn = 1
""")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Copy the chosen files to the destination folder, and log the run

# COMMAND ----------

staged = spark.table(f"{fqn}.af_files_staged").collect()
copied = 0
for r in staged:
    dbutils.fs.cp(r["path"], f"{dest}/{r['file_name']}")
    copied += 1

spark.sql(f"""CREATE TABLE IF NOT EXISTS {fqn}.af_staging_audit
  (run_ts TIMESTAMP, files_seen INT, codes INT, files_staged INT, files_copied INT)""")
spark.sql(f"""INSERT INTO {fqn}.af_staging_audit
  SELECT current_timestamp(),
         (SELECT count(*) FROM {fqn}.af_files_bronze),
         (SELECT count(DISTINCT concat(folder, report_code)) FROM {fqn}.af_files_staged),
         (SELECT count(*) FROM {fqn}.af_files_staged), {copied}""")

print(f"seen {spark.table(f'{fqn}.af_files_bronze').count()} files · "
      f"staged {len(staged)} (one per folder+code) · copied {copied} to destination")
display(spark.sql(f"SELECT folder, report_code, version, file_name FROM {fqn}.af_files_staged ORDER BY folder, report_code"))
print("Destination now holds:", [f.name for f in dbutils.fs.ls(dest)])
display(spark.sql(f"SELECT * FROM {fqn}.af_staging_audit ORDER BY run_ts DESC"))
print("Schedule as a Lakeflow Job (monthly) or let Autoloader fire on arrival. Every run appends "
      "to af_staging_audit; Job run history + system.access.audit complete the trail — no manual moves.")
