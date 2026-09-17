# Databricks notebook source
# MAGIC %md
# MAGIC # UC1 · Ingest the bank workbooks with Autoloader
# MAGIC
# MAGIC The bank drops each account's rec workbook into a Volume folder. **Autoloader** picks up every new
# MAGIC file the moment it lands, and the ingest reads the `Header` sheet's **8 reconciliation figures**
# MAGIC (opening/closing O/S items and balances per SAP and per Bank) into **`cf_period_extract`** — this
# MAGIC period's numbers, one row per account × line. That table is a source for the Designer flow.
# MAGIC
# MAGIC - **Landing (bank drops here):** `…/uc1/bank_recs/`  ·  **Fallback (workbook missing):** `…/uc1/fallback/`
# MAGIC - **Produces:** `cf_period_extract` (+ `cf_ingest_log`, `cf_bank_files_bronze`)

# COMMAND ----------

# MAGIC %pip install openpyxl -q
# MAGIC dbutils.library.restartPython()

# COMMAND ----------

dbutils.widgets.text("catalog_name", "lr_dev_aws_us_catalog")
dbutils.widgets.text("schema_name", "designer_recon_demo")
dbutils.widgets.text("landing_volume_name", "recon_landing")
dbutils.widgets.text("period", "2026-07")
catalog = dbutils.widgets.get("catalog_name"); schema = dbutils.widgets.get("schema_name")
volume = dbutils.widgets.get("landing_volume_name"); period = dbutils.widgets.get("period")
fqn = f"{catalog}.{schema}"
vroot = f"/Volumes/{catalog}/{schema}/{volume}/uc1"
schema_loc = f"{vroot}/_ingest_schema"; checkpoint = f"{vroot}/_ingest_checkpoint"

BANK_ROWS = {"Opening Balance per Bank", "Closing Balance per Bank"}
CATS = ["Opening O/S items on SAP not on bank", "Opening O/S items on bank not on SAP",
        "Opening Balance per SAP", "Opening Balance per Bank",
        "Closing O/S items on SAP not on Bank", "Closing O/S items on bank not on SAP",
        "Closing Balance per SAP", "Closing Balance per Bank"]

# COMMAND ----------

# MAGIC %md
# MAGIC ## Autoloader picks up every workbook that has landed (fires on arrival)

# COMMAND ----------

spark.sql(f"DROP TABLE IF EXISTS {fqn}.cf_bank_files_bronze")
dbutils.fs.rm(checkpoint, True); dbutils.fs.rm(schema_loc, True)   # reprocess every file each run — standalone-safe
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
# MAGIC ## Read the 8 header figures per account (fallback = 2 cells) → `cf_period_extract`

# COMMAND ----------

import os, glob
import pandas as pd
from io import BytesIO
from openpyxl import load_workbook

def read_header(content):
    ws = load_workbook(BytesIO(content), data_only=True)["Header"]
    acct, kv = None, {}
    for r in range(1, ws.max_row + 1):
        a = ws[f"A{r}"].value
        if a is None: continue
        a = str(a).strip()
        if a == "Account Number": acct = str(ws[f"B{r}"].value).strip()
        if a in CATS: kv[a] = (ws[f"B{r}"].value, ws[f"D{r}"].value)   # value, Control (bank rows only)
    return acct, kv

rows, log = [], []
for r in spark.table(f"{fqn}.cf_bank_files_bronze").select("path", "content").collect():
    fname = os.path.basename(r["path"])
    try:                                        # fail SAFE — a bad workbook is quarantined + logged, never silently ingested
        acct, kv = read_header(r["content"])
        for cat, (val, ctl) in kv.items():
            rows.append({"Account No.": acct, "Category": cat, "current_period": round(float(val), 2),
                         "period_control": (round(float(ctl), 2) if cat in BANK_ROWS and ctl is not None else None),
                         "source": "bank_rec", "source_file": fname})
        log.append({"source_file": fname, "account_code": acct, "status": "ok", "detail": f"read {len(kv)} header figures"})
    except Exception as e:
        log.append({"source_file": fname, "account_code": None, "status": "FAILED", "detail": str(e)[:180]})

# fallback: 2 cells — Closing Balance per SAP (SAP xlsx) + Closing Balance per Bank (bank statement csv)
for sp in glob.glob(f"{vroot}/fallback/SAP Bank balances*.xlsx"):
    sap_v = float(pd.read_excel(sp, engine="openpyxl")["Amt Cum.lc.cur"].iloc[0])
    csv = glob.glob(f"{vroot}/fallback/Bank Statement balances*.csv")[0]
    bs = pd.read_csv(csv, skiprows=1, dtype={"ACCT NO": str})   # row 1 is the export title; keep leading zeros
    acct = str(bs["ACCT NO"].iloc[0]).strip()
    bank_v = float(str(bs["STMT BAL"].iloc[0]).replace(",", ""))
    rows += [
        {"Account No.": acct, "Category": "Closing Balance per SAP",  "current_period": round(sap_v, 2),  "period_control": None,
         "source": "fallback", "source_file": os.path.basename(sp)},
        {"Account No.": acct, "Category": "Closing Balance per Bank", "current_period": round(bank_v, 2),
         "period_control": round(bank_v - sap_v, 2), "source": "fallback", "source_file": os.path.basename(csv)},
    ]
    log.append({"source_file": "fallback (SAP xlsx + bank csv)", "account_code": acct, "status": "ok", "detail": "2-cell fallback — workbook missing"})

extract = pd.DataFrame(rows)
(spark.createDataFrame(extract.astype(object).where(pd.notnull(extract), None)).write.mode("overwrite")
    .option("overwriteSchema", "true").option("delta.columnMapping.mode", "name").saveAsTable(f"{fqn}.cf_period_extract"))
spark.sql(f"COMMENT ON TABLE {fqn}.cf_period_extract IS 'UC1 this-period figures ingested via Autoloader (long: account x line); source_file = provenance. Synthetic.'")

ilog = pd.DataFrame(log).sort_values(["status", "source_file"])
spark.createDataFrame(ilog).write.mode("overwrite").option("overwriteSchema", "true").saveAsTable(f"{fqn}.cf_ingest_log")
spark.sql(f"COMMENT ON TABLE {fqn}.cf_ingest_log IS 'UC1 ingest audit: one row per file — ok or FAILED (bad file quarantined). Synthetic.'")

n_ok = int((ilog.status == "ok").sum()); n_bad = int((ilog.status == "FAILED").sum())
print(f"cf_period_extract: {len(extract)} rows across {extract['Account No.'].nunique()} accounts · ingest log: {n_ok} ok, {n_bad} FAILED")
display(spark.table(f"{fqn}.cf_ingest_log"))
