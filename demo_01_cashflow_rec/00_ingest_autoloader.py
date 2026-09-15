# Databricks notebook source
# MAGIC %md
# MAGIC # UC1 · Ingest the bank workbooks with Autoloader
# MAGIC
# MAGIC The bank drops each account's rec workbook into a Volume folder. **Autoloader** picks up every
# MAGIC new file the moment it lands (no one moves or opens anything), and the ingest reads the header
# MAGIC cells (SAP / Accurate / Bank / Control) into one tidy table, **`cf_period_extract`** — this
# MAGIC month's numbers, one row per account. That table is then a source for the Designer flow.
# MAGIC
# MAGIC - **Landing folder (bank drops here):** `…/recon_landing/uc1/bank_recs/`
# MAGIC - **Fallback (workbook missing):** `…/uc1/sap_fallback/` + `…/uc1/bank_fallback/`
# MAGIC - **Produces:** `cf_period_extract`  ·  **Also lands:** `cf_bank_files_bronze` (what Autoloader saw)

# COMMAND ----------

# MAGIC %pip install openpyxl -q
# MAGIC dbutils.library.restartPython()

# COMMAND ----------

dbutils.widgets.text("catalog_name", "lr_dev_aws_us_catalog")
dbutils.widgets.text("schema_name", "designer_recon_demo")
dbutils.widgets.text("landing_volume_name", "recon_landing")
dbutils.widgets.text("period", "2026-07")
catalog = dbutils.widgets.get("catalog_name")
schema = dbutils.widgets.get("schema_name")
volume = dbutils.widgets.get("landing_volume_name")
period = dbutils.widgets.get("period")
fqn = f"{catalog}.{schema}"
vroot = f"/Volumes/{catalog}/{schema}/{volume}/uc1"
schema_loc = f"{vroot}/_ingest_schema"
checkpoint = f"{vroot}/_ingest_checkpoint"

# COMMAND ----------

# MAGIC %md
# MAGIC ## Autoloader picks up every workbook that has landed (fires on arrival)

# COMMAND ----------

spark.sql(f"DROP TABLE IF EXISTS {fqn}.cf_bank_files_bronze")
(spark.readStream.format("cloudFiles")
    .option("cloudFiles.format", "binaryFile")
    .option("cloudFiles.schemaLocation", schema_loc)
    .load(f"{vroot}/bank_recs")
    .selectExpr("path", "length", "content")
    .writeStream.option("checkpointLocation", checkpoint)
    .trigger(availableNow=True)
    .toTable(f"{fqn}.cf_bank_files_bronze")).awaitTermination()

print("Autoloader saw", spark.table(f"{fqn}.cf_bank_files_bronze").count(), "workbooks")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Read the header cells → this month's numbers (`cf_period_extract`)

# COMMAND ----------

import os, glob
import pandas as pd
from io import BytesIO
from openpyxl import load_workbook

def header_of(content):
    ws = load_workbook(BytesIO(content), data_only=True)["Header"]
    return {str(ws[f"A{r}"].value): ws[f"B{r}"].value for r in range(2, 6) if ws[f"A{r}"].value is not None}

rows = []
for r in spark.table(f"{fqn}.cf_bank_files_bronze").select("path", "content").collect():
    code = os.path.basename(r["path"]).replace("BankRec_", "").replace(f"_{period}.xlsx", "")
    h = header_of(r["content"])
    rows.append({"account_code": code, "current_period": round(float(h["Bank"]), 2),
                 "period_control": round(float(h["SAP"]) - float(h["Bank"]), 2), "source": "bank_rec"})

# fallback: 2 cells (SAP + Bank) for accounts whose workbook never landed
sap_fb = {os.path.basename(p).replace("SAP_", "").replace(f"_{period}.csv", ""): pd.read_csv(p)["SAP"][0]
          for p in glob.glob(f"{vroot}/sap_fallback/SAP_*_{period}.csv")}
bank_fb = {os.path.basename(p).replace("Bank_", "").replace(f"_{period}.csv", ""): pd.read_csv(p)["Bank"][0]
           for p in glob.glob(f"{vroot}/bank_fallback/Bank_*_{period}.csv")}
for code in sorted(sap_fb):
    rows.append({"account_code": code, "current_period": round(float(bank_fb[code]), 2),
                 "period_control": round(float(sap_fb[code]) - float(bank_fb[code]), 2), "source": "fallback"})

extract = pd.DataFrame(rows).sort_values("account_code")
spark.createDataFrame(extract).write.mode("overwrite").option("overwriteSchema", "true").saveAsTable(f"{fqn}.cf_period_extract")
spark.sql(f"COMMENT ON TABLE {fqn}.cf_period_extract IS 'UC1 this-period numbers, ingested from the bank workbooks via Autoloader (+2-cell fallback). Synthetic.'")

print(f"cf_period_extract: {len(extract)} accounts "
      f"({(extract.source=='bank_rec').sum()} workbook, {(extract.source=='fallback').sum()} fallback)")
display(spark.table(f"{fqn}.cf_period_extract"))
