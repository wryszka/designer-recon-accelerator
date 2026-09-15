# Databricks notebook source
# MAGIC %md
# MAGIC # UC1 · Generate the synthetic sources (kept deliberately small)
# MAGIC
# MAGIC **6 accounts** so the folder and tables stay legible — a few input examples + one output
# MAGIC example, nothing more. Scale up later if they ask.
# MAGIC
# MAGIC Lands, in the `recon_landing` Volume under `uc1/`:
# MAGIC - `bank_recs/` — **5** account workbooks (`.xlsx`, a `Header` sheet: SAP / Accurate / Bank / Control)
# MAGIC - `fallback/` — the **1** account with no workbook → `SAP_*.csv` + `Bank_*.csv` (2-cell fallback)
# MAGIC - `rolling/` — last month's rolling file `CashFlowRec_2026-06.xlsx` **and** `.csv` (the file you drag)
# MAGIC
# MAGIC Tables: `cf_accounts`, `cf_prior_rec` (rolling baseline), `cf_benchmark` (expected output, the
# MAGIC parity oracle). This-month's `cf_period_extract` is produced by the **Autoloader ingest** (`00_`).

# COMMAND ----------

# MAGIC %pip install openpyxl -q
# MAGIC dbutils.library.restartPython()

# COMMAND ----------

dbutils.widgets.text("catalog_name", "lr_dev_aws_us_catalog")
dbutils.widgets.text("schema_name", "designer_recon_demo")
dbutils.widgets.text("landing_volume_name", "recon_landing")
dbutils.widgets.text("period", "2026-07")
dbutils.widgets.text("fy_start_month", "4")
dbutils.widgets.text("seed", "71")
catalog = dbutils.widgets.get("catalog_name"); schema = dbutils.widgets.get("schema_name")
volume = dbutils.widgets.get("landing_volume_name"); period = dbutils.widgets.get("period")
fy_start_month = int(dbutils.widgets.get("fy_start_month")); seed = int(dbutils.widgets.get("seed"))
fqn = f"{catalog}.{schema}"

spark.sql(f"CREATE SCHEMA IF NOT EXISTS {fqn}")
spark.sql(f"CREATE VOLUME IF NOT EXISTS {fqn}.{volume}")

# COMMAND ----------

import os, shutil, tempfile
import numpy as np, pandas as pd
from openpyxl import Workbook

TMP = tempfile.mkdtemp()
rng = np.random.default_rng(seed)

cur = pd.Period(period, freq="M")
start_year = cur.year if cur.month >= fy_start_month else cur.year - 1
periods = pd.period_range(pd.Period(f"{start_year}-{fy_start_month:02d}", freq="M"), cur, freq="M")
prior_periods = periods[:-1]
cur_label = cur.strftime("%b")
def cols_for(p): return f"{p.strftime('%b')}_Current", f"{p.strftime('%b')}_Control"

vroot = f"/Volumes/{catalog}/{schema}/{volume}/uc1"
shutil.rmtree(vroot, ignore_errors=True)                       # start clean & simple
for sub in ["bank_recs", "fallback", "rolling", "output"]:
    os.makedirs(f"{vroot}/{sub}", exist_ok=True)

# COMMAND ----------

# ---- 6 accounts: 5 with workbooks (1 an exception), 1 missing → fallback ----
N = 6
codes = [f"ACC-{i:03d}" for i in range(1, N + 1)]
accounts = pd.DataFrame({"account_code": codes,
                         "account_name": [f"Operating account {i:03d}" for i in range(1, N + 1)],
                         "currency": "GBP"})
missing_i, exception_i = 5, 2                                   # ACC-006 missing; ACC-003 an exception
base = np.round(rng.uniform(100_000, 3_000_000, N), 2)

# prior rolling file (Apr..Jun), history fully reconciled (control 0)
prior = accounts[["account_code", "account_name"]].copy()
level = base.copy()
for p in prior_periods:
    level = np.round(level + rng.normal(0, 60_000, N), 2)
    c_cur, c_ctl = cols_for(p); prior[c_cur] = level; prior[c_ctl] = 0.0

# this period's true numbers
bank = np.round(level + rng.normal(0, 60_000, N), 2)
sap = bank.copy(); sap[exception_i] = np.round(bank[exception_i] + 420.50, 2)
control = np.round(sap - bank, 2)

# COMMAND ----------

# ---- land the input files ----
def write_workbook(code, sap_v, acc_v, bank_v, ctl_v):
    wb = Workbook(); hs = wb.active; hs.title = "Header"
    hs["A1"], hs["B1"] = "Metric", "Value"
    for r, (lab, val) in enumerate([("SAP", sap_v), ("Accurate", acc_v), ("Bank", bank_v), ("Control", ctl_v)], 2):
        hs[f"A{r}"], hs[f"B{r}"] = lab, float(val)
    tmp = f"{TMP}/{code}.xlsx"; wb.save(tmp)
    shutil.copy(tmp, f"{vroot}/bank_recs/BankRec_{code}_{period}.xlsx")

for i, code in enumerate(codes):
    if i == missing_i:                                         # no workbook → 2-cell fallback
        pd.DataFrame({"account_code": [code], "SAP": [float(sap[i])]}).to_csv(f"{vroot}/fallback/SAP_{code}_{period}.csv", index=False)
        pd.DataFrame({"account_code": [code], "Bank": [float(bank[i])]}).to_csv(f"{vroot}/fallback/Bank_{code}_{period}.csv", index=False)
    else:
        write_workbook(code, sap[i], bank[i], bank[i], control[i])

# rolling file the user drags — xlsx AND csv
prior.to_excel(f"{TMP}/roll.xlsx", index=False, sheet_name="CashFlowRec"); shutil.copy(f"{TMP}/roll.xlsx", f"{vroot}/rolling/CashFlowRec_{prior_periods[-1]}.xlsx")
prior.to_csv(f"{vroot}/rolling/CashFlowRec_{prior_periods[-1]}.csv", index=False)

# COMMAND ----------

# ---- baseline + oracle tables ----
c_cur, c_ctl = cols_for(cur)
benchmark = prior.copy()
benchmark[c_cur] = bank; benchmark[c_ctl] = control
benchmark[f"{cur_label}_Status"] = np.where(np.abs(control) < 0.01, "Reconciled", "Exception")

def write(df, name, comment):
    spark.createDataFrame(df).write.mode("overwrite").option("overwriteSchema", "true").saveAsTable(f"{fqn}.{name}")
    spark.sql(f"COMMENT ON TABLE {fqn}.{name} IS '{comment}'")

write(accounts, "cf_accounts", "UC1 account reference (synthetic).")
write(prior, "cf_prior_rec", "UC1 rolling cash-flow file at prior period — the running baseline (wide). Synthetic.")
write(benchmark, "cf_benchmark", "UC1 expected output: prior + this period Current/Control/Status. Parity oracle. Synthetic.")

print(f"{N} accounts · 5 workbooks + 1 fallback · exception = {codes[exception_i]} (Control {control[exception_i]:+.2f})")
print("landed:", {sub: os.listdir(f'{vroot}/{sub}') for sub in ['bank_recs', 'fallback', 'rolling']})
display(spark.table(f"{fqn}.cf_benchmark"))
