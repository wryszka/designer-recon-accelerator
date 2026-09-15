# Databricks notebook source
# MAGIC %md
# MAGIC # UC3b · Fixed-width BDX files → parse, per-file contra check, consolidate, log
# MAGIC
# MAGIC The Avantia BDX job. Each day a **fixed-width** file lands in a folder. At the start of the
# MAGIC month you run through **all of last month's files** (~30), and for each one:
# MAGIC 1. **parse by position** (it's fixed-width, not delimited — you can't just text-to-columns),
# MAGIC 2. tag every row with the **file it came from**,
# MAGIC 3. run the **contra check**: the detail rows must **sum to the file's contra row**
# MAGIC    (e.g. 10 + 20 + 30 = 60),
# MAGIC 4. **consolidate** all files into one output, and
# MAGIC 5. emit a **run log / summary** — which files ran and whether each tied to its contra.
# MAGIC
# MAGIC A Python-shaped **Lakeflow Job** (not a Designer transform): runs monthly, unattended, with a
# MAGIC full audit trail. Everything synthetic, prefixed `fw_`.

# COMMAND ----------

dbutils.widgets.text("catalog_name", "lr_dev_aws_us_catalog")
dbutils.widgets.text("schema_name", "designer_recon_demo")
dbutils.widgets.text("landing_volume_name", "recon_landing")
dbutils.widgets.text("period", "2026-06")     # the month whose daily files we process
dbutils.widgets.text("seed", "73")
catalog = dbutils.widgets.get("catalog_name")
schema = dbutils.widgets.get("schema_name")
volume = dbutils.widgets.get("landing_volume_name")
period = dbutils.widgets.get("period")
seed = int(dbutils.widgets.get("seed"))
fqn = f"{catalog}.{schema}"
spark.sql(f"CREATE SCHEMA IF NOT EXISTS {fqn}")
spark.sql(f"CREATE VOLUME IF NOT EXISTS {fqn}.{volume}")

vroot = f"/Volumes/{catalog}/{schema}/{volume}/uc3b"
incoming = f"{vroot}/incoming"
output = f"{vroot}/output"

# COMMAND ----------

# MAGIC %md
# MAGIC ## Generate ~30 daily fixed-width files
# MAGIC Layout (1-indexed): `rtype[1] seq[2:6] sort_code[7:12] account[13:20] payee[21:44] amount_pence[45:60]`.
# MAGIC Rows are `D` (detail) then one `C` (contra) whose amount equals the sum of the details.
# MAGIC A couple of days are seeded to **not** tie — so the log has something to catch.

# COMMAND ----------

import calendar, numpy as np, pandas as pd
rng = np.random.default_rng(seed)

dbutils.fs.rm(vroot, True)
dbutils.fs.mkdirs(incoming)

yr, mo = map(int, period.split("-"))
n_days = calendar.monthrange(yr, mo)[1]
mismatch_days = set(int(x) for x in rng.choice(range(1, n_days + 1), size=2, replace=False))
no_contra_day = int(rng.choice([d for d in range(1, n_days + 1) if d not in mismatch_days]))  # one file arrives without its contra row

def rec(rtype, seq, sort, acct, payee, pence):
    return f"{rtype:<1}{seq:<5}{sort:<6}{acct:<8}{payee:<24}{str(int(pence)):<16}"

for d in range(1, n_days + 1):
    k = int(rng.integers(5, 16))
    lines, total = [], 0
    for i in range(k):
        pence = int(rng.integers(1_000, 500_000))
        total += pence
        lines.append(rec("D", i + 1, str(rng.integers(100000, 999999)),
                         str(rng.integers(10_000_000, 99_999_999)), f"Payee {i:04d}", pence))
    if d != no_contra_day:                                          # this one is missing its contra row → must be FLAGGED, not skipped
        contra = total + (int(rng.integers(50, 500)) * 100 if d in mismatch_days else 0)
        lines.append(rec("C", 99999, "", "", "CONTRA TOTAL", contra))
    dbutils.fs.put(f"{incoming}/BDX_{yr}-{mo:02d}-{d:02d}.txt", "\n".join(lines) + "\n", True)

print(f"wrote {n_days} daily files for {period}; contra broken on days {sorted(mismatch_days)}; no contra row on day {no_contra_day}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Parse by position across all files, keeping the source file name

# COMMAND ----------

from pyspark.sql import functions as F

raw = spark.read.text(incoming).select("value", F.col("_metadata.file_name").alias("source_file"))
parsed = raw.selectExpr(
    "source_file",
    "trim(substring(value, 1, 1))                             AS record_type",
    "trim(substring(value, 2, 5))                             AS seq",
    "trim(substring(value, 7, 6))                             AS sort_code",
    "trim(substring(value, 13, 8))                            AS account_no",
    "trim(substring(value, 21, 24))                           AS payee_name",
    "try_cast(trim(substring(value, 45, 16)) AS DOUBLE)/100.0 AS amount",
).where("length(trim(value)) > 0")

# consolidate all files' DETAIL rows into one table
detail = parsed.where("record_type = 'D'")
detail.write.mode("overwrite").option("overwriteSchema", "true").saveAsTable(f"{fqn}.fw_bdx_consolidated")
spark.sql(f"COMMENT ON TABLE {fqn}.fw_bdx_consolidated IS 'UC3b consolidated detail rows across all daily fixed-width files (synthetic).'")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Per-file contra check: detail rows must sum to the contra row

# COMMAND ----------

# start from EVERY file that landed, so an empty / no-contra file can't silently vanish
# value-level integrity, not just file-count: a row whose amount doesn't parse must NOT silently become 0
all_files = spark.createDataFrame([(f.name,) for f in dbutils.fs.ls(incoming)], "source_file string")
detail_agg = detail.groupBy("source_file").agg(
    F.count("*").alias("detail_rows"),
    F.sum(F.when(F.col("amount").isNull(), 1).otherwise(0)).alias("unparsed_rows"),   # amount failed to parse → flag it
    F.round(F.sum("amount"), 2).alias("detail_sum"))
contra = parsed.where("record_type = 'C'").groupBy("source_file").agg(
    F.count("*").alias("contra_rows"), F.round(F.sum("amount"), 2).alias("contra_amount"))

log = (all_files.join(detail_agg, "source_file", "left").join(contra, "source_file", "left")
       .withColumn("difference", F.round(F.col("detail_sum") - F.col("contra_amount"), 2))
       .withColumn("status",
           F.when(F.col("detail_rows").isNull(), "EMPTY")
            .when(F.col("unparsed_rows") > 0, "PARSE ISSUE")        # a shifted/ragged line — caught, not summed as 0
            .when(F.col("contra_rows") > 1, "MULTI CONTRA")         # a second contra row — caught, not double-counted
            .when(F.col("contra_amount").isNull(), "NO CONTRA")
            .when(F.abs("difference") < 0.005, "MATCH")
            .otherwise("MISMATCH")))
log.write.mode("overwrite").option("overwriteSchema", "true").saveAsTable(f"{fqn}.fw_contra_log")
spark.sql(f"COMMENT ON TABLE {fqn}.fw_contra_log IS 'UC3b per-file reconciliation — every landed file statused MATCH / MISMATCH / NO CONTRA / PARSE ISSUE / MULTI CONTRA / EMPTY (value-level, not just file count). Synthetic.'")
assert spark.table(f"{fqn}.fw_contra_log").count() == all_files.count(), "a landed file is missing from the log"

# COMMAND ----------

# MAGIC %md
# MAGIC ## Consolidated CSV output + a run summary (the "email at the end")

# COMMAND ----------

(spark.table(f"{fqn}.fw_bdx_consolidated").coalesce(1)
    .write.mode("overwrite").option("header", True).csv(f"{output}/consolidated_{period}"))

counts = {r["status"]: r["n"] for r in spark.sql(f"SELECT status, count(*) n FROM {fqn}.fw_contra_log GROUP BY status").collect()}
total_files = sum(counts.values())
bad = spark.sql(f"SELECT source_file, status, difference FROM {fqn}.fw_contra_log WHERE status <> 'MATCH' ORDER BY status, source_file").collect()
summary = (f"BDX consolidation — {period}\n"
           f"files processed : {total_files} (every landed file accounted for)\n"
           + "".join(f"  {st:<13}: {counts[st]}\n" for st in sorted(counts))
           + ("".join(f"  ! {r['source_file']}  {r['status']}  diff {r['difference'] if r['difference'] is not None else '-'}\n" for r in bad)
              if bad else "  all files tied to their contra row\n"))
dbutils.fs.put(f"{output}/run_summary_{period}.txt", summary, True)
print(summary)
print(f"consolidated CSV → {output}/consolidated_{period}/   ·   summary → {output}/run_summary_{period}.txt")
display(spark.sql(f"SELECT * FROM {fqn}.fw_contra_log ORDER BY status DESC, source_file"))
