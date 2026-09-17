# Databricks notebook source
# MAGIC %md
# MAGIC # UC3b · Fixed-width payment submissions → parse, per-file contra, consolidate, log
# MAGIC
# MAGIC Monthly, **fixed-width payment submission files** land from **two sources** (`SRC_A`, `SRC_B`). For each:
# MAGIC 1. **parse by column position** (it's fixed-width, not delimited),
# MAGIC 2. tag every row with its **source file** and **FileType** (which source),
# MAGIC 3. **contra check**: the detail rows (**Trans Code 99**) must sum to the file's **contra row (Trans Code 17)**,
# MAGIC 4. **consolidate** all files into one output, and
# MAGIC 5. emit a **run log / summary** — which files ran and whether each tied.
# MAGIC
# MAGIC A Python-shaped **Lakeflow Job** (not a Designer transform): monthly, unattended, fully audited.
# MAGIC Everything synthetic — **no real names, sort codes, accounts or payees** — prefixed `fw_`.

# COMMAND ----------

dbutils.widgets.text("catalog_name", "lr_dev_aws_us_catalog")
dbutils.widgets.text("schema_name", "designer_recon_demo")
dbutils.widgets.text("landing_volume_name", "recon_landing")
dbutils.widgets.text("period", "2026-09")
dbutils.widgets.text("seed", "73")
catalog = dbutils.widgets.get("catalog_name"); schema = dbutils.widgets.get("schema_name")
volume = dbutils.widgets.get("landing_volume_name"); period = dbutils.widgets.get("period"); seed = int(dbutils.widgets.get("seed"))
fqn = f"{catalog}.{schema}"
spark.sql(f"CREATE SCHEMA IF NOT EXISTS {fqn}"); spark.sql(f"CREATE VOLUME IF NOT EXISTS {fqn}.{volume}")
vroot = f"/Volumes/{catalog}/{schema}/{volume}/uc3b"; incoming = f"{vroot}/incoming"; output = f"{vroot}/output"

# COMMAND ----------

# MAGIC %md
# MAGIC ## Generate fixed-width submission files from two sources
# MAGIC Layout (1-indexed): `recipient_sort[1:6] recipient_acct[7:14] trans_code[15:16] payers_sort[17:22]`
# MAGIC `payers_acct[23:30] amount_pence[31:41] reference[42:59] payee_name[60:83]`.
# MAGIC Rows are `99` (detail) then one `17` (contra) whose amount equals the sum of the details.

# COMMAND ----------

import numpy as np
rng = np.random.default_rng(seed)
dbutils.fs.rm(vroot, True); dbutils.fs.mkdirs(incoming)
yr, mo = map(int, period.split("-"))

def rec(sort, acct, tcode, psort, pacct, pence, ref, payee):
    return f"{sort:<6}{acct:<8}{tcode:<2}{psort:<6}{pacct:<8}{str(int(pence)):<11}{ref:<18}{payee:<24}"

# 6 submission files: SRC_A x3, SRC_B x3. Inject: 1 mismatch, 1 no-contra, 1 parse-issue (a shifted line).
files = [("SRC_A", 1), ("SRC_A", 3), ("SRC_A", 5), ("SRC_B", 2), ("SRC_B", 4), ("SRC_B", 8)]
mismatch_idx, no_contra_idx, parse_idx = 1, 4, 2                       # positions in `files`
for idx, (src, day) in enumerate(files):
    k = int(rng.integers(5, 13)); lines, total = [], 0
    for i in range(k):
        pence = int(rng.integers(5_000, 900_000)); total += pence
        line = rec(f"{rng.integers(100000,999999)}", f"{rng.integers(10000000,99999999)}", "99",
                   f"{rng.integers(100000,999999)}", f"{rng.integers(1000000,9999999)}", pence,
                   f"REF{rng.integers(100000,999999)}", f"Payee {i:03d}")
        if idx == parse_idx and i == 0:
            line = line[:30] + "N/A".ljust(11) + line[41:]            # non-numeric amount -> PARSE ISSUE (never summed as 0)
        lines.append(line)
    if idx != no_contra_idx:                                          # this file arrives without its contra row -> NO CONTRA
        contra = total + (rng.integers(50, 500) * 100 if idx == mismatch_idx else 0)
        lines.append(rec("000000", "00000000", "17", "000000", "0000000", contra, "CONTRA", "CONTRA TOTAL"))
    dbutils.fs.put(f"{incoming}/{src}_SUBMISSION_{yr}{mo:02d}{day:02d}.txt", "\n".join(lines) + "\n", True)

print(f"wrote {len(files)} submission files ({period}); mismatch on file {mismatch_idx}, no-contra on {no_contra_idx}, parse-issue on {parse_idx}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Parse by position across all files, keeping source file + FileType

# COMMAND ----------

from pyspark.sql import functions as F
raw = spark.read.text(incoming).select("value", F.col("_metadata.file_name").alias("source_file"))
parsed = raw.selectExpr(
    "source_file",
    "regexp_extract(source_file, '^(SRC_[AB])', 1)          AS file_type",
    "trim(substring(value, 1, 6))                           AS recipient_sort_code",
    "trim(substring(value, 7, 8))                           AS recipient_account_no",
    "trim(substring(value, 15, 2))                          AS trans_code",
    "trim(substring(value, 17, 6))                          AS payers_sort_code",
    "trim(substring(value, 23, 8))                          AS payers_account_no",
    "try_cast(trim(substring(value, 31, 11)) AS DOUBLE)/100.0 AS amount",
    "trim(substring(value, 42, 18))                         AS reference",
    "trim(substring(value, 60, 24))                         AS payee_name",
).where("length(trim(value)) > 0")

detail = parsed.where("trans_code = '99'")
detail.write.mode("overwrite").option("overwriteSchema", "true").saveAsTable(f"{fqn}.fw_bdx_consolidated")
spark.sql(f"COMMENT ON TABLE {fqn}.fw_bdx_consolidated IS 'UC3b consolidated detail (Trans Code 99) rows across both sources, tagged by FileType. Synthetic.'")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Per-file contra check: detail rows (99) must sum to the contra row (17)

# COMMAND ----------

# start from EVERY file that landed, so an empty / no-contra file can't silently vanish; a row whose amount
# doesn't parse must NOT silently become 0
all_files = spark.createDataFrame([(f.name,) for f in dbutils.fs.ls(incoming)], "source_file string")
detail_agg = detail.groupBy("source_file").agg(
    F.count("*").alias("detail_rows"),
    F.sum(F.when(F.col("amount").isNull(), 1).otherwise(0)).alias("unparsed_rows"),
    F.round(F.sum("amount"), 2).alias("detail_sum"))
contra = parsed.where("trans_code = '17'").groupBy("source_file").agg(
    F.count("*").alias("contra_rows"), F.round(F.sum("amount"), 2).alias("contra_amount"))

log = (all_files.join(detail_agg, "source_file", "left").join(contra, "source_file", "left")
       .withColumn("difference", F.round(F.col("detail_sum") - F.col("contra_amount"), 2))
       .withColumn("status",
           F.when(F.col("detail_rows").isNull(), "EMPTY")
            .when(F.col("unparsed_rows") > 0, "PARSE ISSUE")
            .when(F.col("contra_rows") > 1, "MULTI CONTRA")
            .when(F.col("contra_amount").isNull(), "NO CONTRA")
            .when(F.abs("difference") < 0.005, "MATCH")
            .otherwise("MISMATCH")))
log.write.mode("overwrite").option("overwriteSchema", "true").saveAsTable(f"{fqn}.fw_contra_log")
spark.sql(f"COMMENT ON TABLE {fqn}.fw_contra_log IS 'UC3b per-file reconciliation — every landed file statused MATCH / MISMATCH / NO CONTRA / PARSE ISSUE / MULTI CONTRA / EMPTY (value-level). Synthetic.'")
assert spark.table(f"{fqn}.fw_contra_log").count() == all_files.count(), "a landed file is missing from the log"

# COMMAND ----------

# MAGIC %md
# MAGIC ## Consolidated CSV output + a run summary (the "email at the end")

# COMMAND ----------

(spark.table(f"{fqn}.fw_bdx_consolidated").coalesce(1)
    .write.mode("overwrite").option("header", True).csv(f"{output}/consolidated_{period}"))

counts = {r["status"]: r["n"] for r in spark.sql(f"SELECT status, count(*) n FROM {fqn}.fw_contra_log GROUP BY status").collect()}
bad = spark.sql(f"SELECT source_file, status, difference FROM {fqn}.fw_contra_log WHERE status <> 'MATCH' ORDER BY status, source_file").collect()
summary = (f"BDX consolidation — {period}\n"
           f"files processed : {sum(counts.values())} (every landed file accounted for)\n"
           + "".join(f"  {st:<13}: {counts[st]}\n" for st in sorted(counts))
           + ("".join(f"  ! {r['source_file']}  {r['status']}  diff {r['difference'] if r['difference'] is not None else '-'}\n" for r in bad)
              if bad else "  all files tied to their contra row\n"))
dbutils.fs.put(f"{output}/run_summary_{period}.txt", summary, True)
print(summary)
display(spark.sql(f"SELECT * FROM {fqn}.fw_contra_log ORDER BY status DESC, source_file"))
