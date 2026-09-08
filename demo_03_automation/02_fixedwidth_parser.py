# Databricks notebook source
# MAGIC %md
# MAGIC # UC3b · Fixed-width payment file → parse + contra reconciliation
# MAGIC
# MAGIC The second automation: a **fixed-width** payment export (not delimited) is parsed by
# MAGIC column position, contra entries are reconciled, and a consolidated, validated output is
# MAGIC produced. Another Python-shaped job (not a Designer transform) that runs on a schedule
# MAGIC with a full audit trail — the platform answer to "can it do what our script does?".
# MAGIC
# MAGIC Everything synthetic, prefixed `fw_`. No real bank, payer or payee.

# COMMAND ----------

dbutils.widgets.text("catalog_name", "lr_dev_aws_us_catalog")
dbutils.widgets.text("schema_name", "designer_recon_demo")
dbutils.widgets.text("landing_volume_name", "recon_landing")
dbutils.widgets.text("seed", "73")
catalog = dbutils.widgets.get("catalog_name")
schema = dbutils.widgets.get("schema_name")
volume = dbutils.widgets.get("landing_volume_name")
seed = int(dbutils.widgets.get("seed"))
fqn = f"{catalog}.{schema}"
spark.sql(f"CREATE SCHEMA IF NOT EXISTS {fqn}")
spark.sql(f"CREATE VOLUME IF NOT EXISTS {fqn}.{volume}")
src_path = f"/Volumes/{catalog}/{schema}/{volume}/payments_fixedwidth.txt"

# COMMAND ----------

# MAGIC %md
# MAGIC ## Generate a synthetic fixed-width file (self-consistent layout)
# MAGIC Layout (0-indexed slices): sort_code[0:6] account_no[6:14] trans_code[14:17]
# MAGIC amount_pence[17:30] reference[30:48] payment_reference[48:66] payee_name[66:96].
# MAGIC First 4 rows are a header block and are skipped; only rows starting with a digit parse.

# COMMAND ----------

import numpy as np
rng = np.random.default_rng(seed)

def row(sort_code, acct, tcode, pence, ref, pay_ref, payee):
    return (f"{sort_code:<6}{acct:<8}{tcode:<3}{pence:<13}{ref:<18}{pay_ref:<18}{payee:<30}")

lines = ["HEADER  BATCH EXPORT (synthetic)".ljust(96),
         "FILETYPE=PAYMENTS".ljust(96),
         "GENERATED=2026-09-07".ljust(96),
         "----".ljust(96)]
total_pounds = 0.0
for i in range(200):
    pence = int(rng.integers(500, 500000))           # 5.00 – 5,000.00
    is_contra = rng.random() < 0.15
    pay_ref = "CONTRA REVERSAL" if is_contra else f"PAYREF{i:05d}"
    lines.append(row(f"{rng.integers(100000,999999)}", f"{rng.integers(10000000,99999999)}",
                     "099", str(pence), f"REF{i:05d}", pay_ref, f"Payee {i:04d}"))
    total_pounds += (-(pence/100.0) if is_contra else (pence/100.0))

dbutils.fs.put(src_path, "\n".join(lines) + "\n", True)
print(f"wrote {src_path} — {len(lines)} lines; expected reconciled total ≈ {round(total_pounds,2)}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Parse by position, apply contra, consolidate + validate

# COMMAND ----------

raw = spark.read.text(src_path)
spark.sql(f"DROP TABLE IF EXISTS {fqn}.fw_bdx_consolidated")

parsed = raw.selectExpr(
    "substring(value, 1, 6) AS sort_code",
    "substring(value, 7, 8) AS account_no",
    "substring(value, 15, 3) AS trans_code",
    "try_cast(trim(substring(value, 18, 13)) AS DOUBLE) / 100.0 AS amount",
    "trim(substring(value, 31, 18)) AS reference",
    "trim(substring(value, 49, 18)) AS payment_reference",
    "trim(substring(value, 67, 30)) AS payee_name",
    "value",
).where("substring(value,1,1) rlike '^[0-9]'")   # skip header rows

# contra: negate amount where payment_reference contains CONTRA
from pyspark.sql import functions as F
final = parsed.withColumn(
    "amount_adjusted",
    F.when(F.upper("payment_reference").contains("CONTRA"), -F.col("amount")).otherwise(F.col("amount"))
).drop("value")

final.write.mode("overwrite").saveAsTable(f"{fqn}.fw_bdx_consolidated")
spark.sql(f"COMMENT ON TABLE {fqn}.fw_bdx_consolidated IS 'Parsed fixed-width payments + contra-adjusted amounts (synthetic).'")

# validation: reconciled total = sum of contra-adjusted amounts
res = spark.sql(f"""
  SELECT count(*) rows,
         round(sum(amount), 2)          AS gross_total,
         round(sum(amount_adjusted), 2) AS reconciled_total,
         sum(CASE WHEN upper(payment_reference) LIKE '%CONTRA%' THEN 1 ELSE 0 END) AS contra_rows
  FROM {fqn}.fw_bdx_consolidated""")
display(res)
print("gross_total = sum of all amounts; reconciled_total nets the contra reversals — that is "
      "the figure that must tie back to the batch control total.")
