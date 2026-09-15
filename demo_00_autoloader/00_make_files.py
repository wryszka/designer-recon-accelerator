# Databricks notebook source
# MAGIC %md
# MAGIC # Auto Loader mini-demo — make the two example files
# MAGIC
# MAGIC The simplest possible "**folder → table**" story. Two tiny Excel files, same shape:
# MAGIC - **file 1 sits in the landing folder** (ingested on the first run)
# MAGIC - **file 2 waits to be dropped** — drop it in during the demo and the table **appends**
# MAGIC
# MAGIC | Location | What |
# MAGIC |---|---|
# MAGIC | `…/recon_landing/autoloader_demo/landing/` | the folder Auto Loader watches (file 1 is here) |
# MAGIC | `…/recon_landing/autoloader_demo/to_drop/`  | file 2 — drag it into `landing/` live to show the append |

# COMMAND ----------

# MAGIC %pip install openpyxl -q
# MAGIC dbutils.library.restartPython()

# COMMAND ----------

dbutils.widgets.text("catalog_name", "lr_dev_aws_us_catalog")
dbutils.widgets.text("schema_name", "designer_recon_demo")
dbutils.widgets.text("landing_volume_name", "recon_landing")
catalog = dbutils.widgets.get("catalog_name"); schema = dbutils.widgets.get("schema_name")
volume = dbutils.widgets.get("landing_volume_name")
spark.sql(f"CREATE SCHEMA IF NOT EXISTS {catalog}.{schema}")
spark.sql(f"CREATE VOLUME IF NOT EXISTS {catalog}.{schema}.{volume}")

import os, shutil, tempfile
import pandas as pd
vroot = f"/Volumes/{catalog}/{schema}/{volume}/autoloader_demo"
shutil.rmtree(vroot, ignore_errors=True)
for d in ["landing", "to_drop", "csv_versions"]:
    os.makedirs(f"{vroot}/{d}", exist_ok=True)
TMP = tempfile.mkdtemp()

# COMMAND ----------

def make(name, rows, folder):
    df = pd.DataFrame(rows, columns=["txn_date", "account", "amount"])
    df.to_excel(f"{TMP}/{name}.xlsx", index=False, sheet_name="Sheet1")
    shutil.copy(f"{TMP}/{name}.xlsx", f"{vroot}/{folder}/{name}.xlsx")
    df.to_csv(f"{vroot}/csv_versions/{name}.csv", index=False)  # csv version kept OUT of landing/

make("movements_2026-07-01", [("2026-07-01", "ACC-001", 1250.00),
                              ("2026-07-01", "ACC-002", 980.50),
                              ("2026-07-01", "ACC-003", 4300.75)], "landing")   # file 1 — sits
make("movements_2026-07-02", [("2026-07-02", "ACC-001", 610.00),
                              ("2026-07-02", "ACC-004", 2100.00),
                              ("2026-07-02", "ACC-005", 75.25)], "to_drop")     # file 2 — drop live

print("landing/:", os.listdir(f"{vroot}/landing"))
print("to_drop/:", os.listdir(f"{vroot}/to_drop"))
