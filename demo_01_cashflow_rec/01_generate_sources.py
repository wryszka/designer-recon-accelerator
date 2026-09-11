# Databricks notebook source
# MAGIC %md
# MAGIC # UC1 · Cash-flow rec — generate the synthetic sources
# MAGIC
# MAGIC The **monthly cash-flow reconciliation**. Each of ~20 bank accounts has its own bank-rec
# MAGIC workbook sitting in a folder; every month someone opens each one, reads a few summary
# MAGIC cells off its **Header** sheet, and **appends two new columns** (this period's *Current* and
# MAGIC *Control* values) onto a single **rolling cash-flow file** that carries one column-pair per
# MAGIC period across the financial year. If an account's workbook is missing, a **fallback** pulls
# MAGIC two cells from separate SAP and Bank folders instead of four.
# MAGIC
# MAGIC This is the process that forced the "disgusting" 5-input positional hack in the desktop ETL
# MAGIC tool (no variables → the new column's position moves every month). Here we just append two
# MAGIC *named* columns — the problem doesn't exist.
# MAGIC
# MAGIC Everything is synthetic and prefixed `cf_`. Files land in the `recon_landing` UC Volume.
# MAGIC
# MAGIC | Artefact | What it is |
# MAGIC |---|---|
# MAGIC | `…/uc1/bank_recs/BankRec_*.xlsx` | one bank-rec workbook per account; 4 header cells (SAP/Accurate/Bank/Control) |
# MAGIC | `…/uc1/sap_fallback/`, `…/uc1/bank_fallback/` | 2-cell fallback for accounts whose workbook is missing |
# MAGIC | `…/uc1/prior/CashFlowRec_<prior>.xlsx` | last month's rolling file (one Current/Control pair per elapsed period) |
# MAGIC | `cf_accounts` | account reference |
# MAGIC | `cf_prior_rec` | the rolling file as a (wide) table — the running baseline |
# MAGIC | `cf_period_extract` | this period parsed from the files: Current + Control per account (+ source) |
# MAGIC | `cf_benchmark` | prior + the two new columns = the expected output. `02_parity` proves the canvas matches |

# COMMAND ----------

# MAGIC %pip install openpyxl -q
# MAGIC dbutils.library.restartPython()

# COMMAND ----------

dbutils.widgets.text("catalog_name", "lr_dev_aws_us_catalog")
dbutils.widgets.text("schema_name", "designer_recon_demo")
dbutils.widgets.text("landing_volume_name", "recon_landing")
dbutils.widgets.text("period", "2026-07")     # current period being run
dbutils.widgets.text("fy_start_month", "4")   # financial year starts in April
dbutils.widgets.text("seed", "71")

catalog = dbutils.widgets.get("catalog_name")
schema = dbutils.widgets.get("schema_name")
volume = dbutils.widgets.get("landing_volume_name")
period = dbutils.widgets.get("period")
fy_start_month = int(dbutils.widgets.get("fy_start_month"))
seed = int(dbutils.widgets.get("seed"))
fqn = f"{catalog}.{schema}"

spark.sql(f"CREATE SCHEMA IF NOT EXISTS {fqn}")
spark.sql(f"CREATE VOLUME IF NOT EXISTS {fqn}.{volume}")

# COMMAND ----------

import os, shutil
import numpy as np, pandas as pd
from openpyxl import Workbook

rng = np.random.default_rng(seed)

# ---- financial-year periods ----------------------------------------------------------
cur = pd.Period(period, freq="M")
start_year = cur.year if cur.month >= fy_start_month else cur.year - 1
fy_start = pd.Period(f"{start_year}-{fy_start_month:02d}", freq="M")
periods = pd.period_range(fy_start, cur, freq="M")        # Apr..Jul (incl. current)
prior_periods = periods[:-1]                               # Apr..Jun
prior_period = prior_periods[-1] if len(prior_periods) else None
cur_label = cur.strftime("%b")                             # "Jul"

def cols_for(p):
    return f"{p.strftime('%b')}_Current", f"{p.strftime('%b')}_Control"

# ---- volume layout -------------------------------------------------------------------
vroot = f"/Volumes/{catalog}/{schema}/{volume}/uc1"
for sub in ["bank_recs", "sap_fallback", "bank_fallback", "prior", "output"]:
    os.makedirs(f"{vroot}/{sub}", exist_ok=True)
# clean prior run of this period's inputs so re-runs are idempotent
for sub in ["bank_recs", "sap_fallback", "bank_fallback", "prior"]:
    for f in os.listdir(f"{vroot}/{sub}"):
        os.remove(f"{vroot}/{sub}/{f}")

# COMMAND ----------

# ---- accounts ------------------------------------------------------------------------
N = 20
CCY = ["GBP", "GBP", "GBP", "GBP", "EUR", "USD"]
HOUSE_BANKS = ["HB01", "HB02", "HB03", "HB04"]
codes = [f"ACC-{i:03d}" for i in range(1, N + 1)]
accounts = pd.DataFrame({
    "account_code": codes,
    "account_name": [f"Operating account {i:03d}" for i in range(1, N + 1)],
    "house_bank": [HOUSE_BANKS[i % len(HOUSE_BANKS)] for i in range(N)],
    "currency": [CCY[i % len(CCY)] for i in range(N)],
})

base = np.round(rng.uniform(50_000, 5_000_000, N), 2)      # per-account scale

# which accounts are missing a workbook this month (→ fallback), and which have a control break
missing_idx = set(rng.choice(N, size=3, replace=False).tolist())
break_idx = set(x for x in rng.choice(N, size=2, replace=False).tolist() if x not in missing_idx)

# ---- prior rolling file (Apr..Jun): one Current/Control pair per period --------------
prior_wide = accounts[["account_code", "account_name"]].copy()
level = base.copy()
for p in prior_periods:
    level = np.round(level + rng.normal(0, 120_000, N), 2)  # gentle drift period to period
    c_cur, c_ctl = cols_for(p)
    prior_wide[c_cur] = level
    prior_wide[c_ctl] = 0.0                                 # history is fully reconciled

# ---- this period's true values -------------------------------------------------------
bank = np.round(level + rng.normal(0, 120_000, N), 2)       # current cash position
sap = bank.copy()
accurate = bank.copy()
for i in break_idx:                                         # a couple of genuine control breaks
    sap[i] = np.round(bank[i] + rng.uniform(150, 900) * rng.choice([-1, 1]), 2)
control = np.round(sap - bank, 2)
source = np.array(["fallback" if i in missing_idx else "bank_rec" for i in range(N)])

# COMMAND ----------

# ---- write the per-account inputs to the Volume --------------------------------------
def write_bank_rec(code, sap_v, acc_v, bank_v, ctl_v):
    wb = Workbook()
    hs = wb.active; hs.title = "Header"
    hs["A1"], hs["B1"] = "Metric", "Value"
    for r, (label, val) in enumerate(
        [("SAP", sap_v), ("Accurate", acc_v), ("Bank", bank_v), ("Control", ctl_v)], start=2):
        hs[f"A{r}"], hs[f"B{r}"] = label, float(val)
    ds = wb.create_sheet("Detail")                          # realism only; not read
    ds.append(["txn_id", "date", "description", "amount"])
    for k in range(5):
        ds.append([f"T{k:04d}", str(cur), "sample movement", round(float(rng.uniform(-9000, 9000)), 2)])
    tmp = f"/tmp/BankRec_{code}_{period}.xlsx"; wb.save(tmp)
    shutil.copy(tmp, f"{vroot}/bank_recs/BankRec_{code}_{period}.xlsx")

for i, code in enumerate(codes):
    if i in missing_idx:
        # fallback: 2 cells only, in two separate folders
        pd.DataFrame({"account_code": [code], "SAP": [float(sap[i])]}).to_csv(
            f"{vroot}/sap_fallback/SAP_{code}_{period}.csv", index=False)
        pd.DataFrame({"account_code": [code], "Bank": [float(bank[i])]}).to_csv(
            f"{vroot}/bank_fallback/Bank_{code}_{period}.csv", index=False)
    else:
        write_bank_rec(code, sap[i], accurate[i], bank[i], control[i])

# prior rolling file as an Excel workbook
if prior_period is not None:
    tmp = f"/tmp/CashFlowRec_{prior_period}.xlsx"
    prior_wide.to_excel(tmp, index=False, sheet_name="CashFlowRec")
    shutil.copy(tmp, f"{vroot}/prior/CashFlowRec_{prior_period}.xlsx")

print(f"period {period} · {N} accounts · {len(missing_idx)} missing→fallback · "
      f"{len(break_idx)} control breaks · prior periods {[str(p) for p in prior_periods]}")

# COMMAND ----------

# ---- tables: reference, rolling baseline, parsed extract, benchmark ------------------
c_cur, c_ctl = cols_for(cur)
period_extract = pd.DataFrame({
    "account_code": codes, "period": str(cur),
    "current_period": bank, "period_control": control, "source": source,
})
benchmark = prior_wide.copy()
benchmark[c_cur] = bank
benchmark[c_ctl] = control

def write(df, name, comment):
    spark.createDataFrame(df).write.mode("overwrite").option("overwriteSchema", "true").saveAsTable(f"{fqn}.{name}")
    spark.sql(f"COMMENT ON TABLE {fqn}.{name} IS '{comment}'")

write(accounts, "cf_accounts", "UC1 bank account reference (synthetic).")
write(prior_wide, "cf_prior_rec", "UC1 rolling cash-flow file as at prior period — the running baseline (wide, one Current/Control pair per period). Synthetic.")
write(period_extract, "cf_period_extract", "UC1 this-period values parsed from the bank-rec workbooks (+2-cell fallback): Current + Control per account. Synthetic.")
write(benchmark, "cf_benchmark", "UC1 expected output: prior rolling file + the two new period columns. Parity oracle for the Designer canvas. Synthetic.")

print(f"appended columns: {c_cur}, {c_ctl}")
display(spark.sql(f"SELECT source, count(*) accounts, round(sum(abs(period_control)),2) total_abs_control FROM {fqn}.cf_period_extract GROUP BY source"))
