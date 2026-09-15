# Databricks notebook source
# MAGIC %md
# MAGIC # UC1 · Append + reconcile + parity + formatted Excel
# MAGIC
# MAGIC The coded mirror of the **Lakeflow Designer** flow — so we can prove it ties out:
# MAGIC 1. join the rolling file (`cf_prior_rec`) to this month's numbers (`cf_period_extract`, from the
# MAGIC    Autoloader ingest) on `account_code`,
# MAGIC 2. derive **`Jul_Status`** = *Reconciled* when Control nets to 0, else *Exception*,
# MAGIC 3. append **`Jul_Current`** / **`Jul_Control`**,
# MAGIC 4. prove it matches the benchmark **to the penny**,
# MAGIC 5. write the **formatted Excel** output (`.xlsx` + `.csv`).
# MAGIC
# MAGIC In the room the Designer canvas does steps 1–3 (no code); this notebook is the receipt.

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

import os, shutil, tempfile
import pandas as pd
cur_label = pd.Period(period, freq="M").strftime("%b")
C_CUR, C_CTL, C_ST = f"{cur_label}_Current", f"{cur_label}_Control", f"{cur_label}_Status"

# COMMAND ----------

# ---- 1–3. join → status → append (this is what the Designer canvas produces) ----
rolling = spark.table(f"{fqn}.cf_prior_rec").toPandas()
extract = spark.table(f"{fqn}.cf_period_extract").toPandas()

out = rolling.merge(extract[["account_code", "current_period", "period_control"]], on="account_code", how="left")
out = out.rename(columns={"current_period": C_CUR, "period_control": C_CTL})
out[C_ST] = out[C_CTL].abs().lt(0.01).map({True: "Reconciled", False: "Exception"})

spark.createDataFrame(out).write.mode("overwrite").option("overwriteSchema", "true").saveAsTable(f"{fqn}.cf_cashflow_rec")
spark.sql(f"COMMENT ON TABLE {fqn}.cf_cashflow_rec IS 'UC1 produced rolling rec: prior + this period Current/Control/Status. Synthetic.'")

# COMMAND ----------

# ---- 4. parity vs the benchmark, to the penny ----
bench = spark.table(f"{fqn}.cf_benchmark").toPandas()
cols = [c for c in bench.columns if c in out.columns]
a = out[cols].sort_values("account_code").reset_index(drop=True)
b = bench[cols].sort_values("account_code").reset_index(drop=True)
num = [c for c in cols if c not in ("account_code", "account_name", C_ST)]
mism = int(((a[num].round(2) - b[num].round(2)).abs() > 0.005).sum().sum())
status_mism = int((a[C_ST] != b[C_ST]).sum())
print(f"PARITY: {'✅ to the penny' if mism == 0 and status_mism == 0 else f'❌ {mism} value / {status_mism} status diffs'}")
assert mism == 0 and status_mism == 0, "parity failed"

# COMMAND ----------

# ---- 5. formatted Excel (+ csv) out ----
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

wb = Workbook(); ws = wb.active; ws.title = f"CashFlowRec {period}"
hdr = PatternFill("solid", fgColor="1B3A4B"); hf = Font(bold=True, color="FFFFFF")
thin = Side(style="thin", color="D9D9D9"); bd = Border(thin, thin, thin, thin)
ws.append(list(out.columns))
for j, c in enumerate(out.columns, 1):
    cell = ws.cell(1, j); cell.fill = hdr; cell.font = hf; cell.alignment = Alignment(horizontal="center"); cell.border = bd
for _, r in out.iterrows():
    ws.append([r[c] for c in out.columns])
for i in range(2, ws.max_row + 1):
    for j, c in enumerate(out.columns, 1):
        cell = ws.cell(i, j); cell.border = bd
        if c.endswith("_Current") or c.endswith("_Control"):
            cell.number_format = "#,##0.00"
        if (c == C_ST and cell.value == "Exception") or (c == C_CTL and isinstance(cell.value, (int, float)) and abs(cell.value) > 0.005):
            cell.font = Font(color="C00000", bold=True)
for j, c in enumerate(out.columns, 1):
    ws.column_dimensions[get_column_letter(j)].width = 22 if c == "account_name" else 14
ws.freeze_panes = "C2"
os.makedirs(f"{vroot}/output", exist_ok=True)
_t = tempfile.mkdtemp(); wb.save(f"{_t}/out.xlsx"); shutil.copy(f"{_t}/out.xlsx", f"{vroot}/output/CashFlowRec_{period}.xlsx")
out.to_csv(f"{vroot}/output/CashFlowRec_{period}.csv", index=False)

recon = int((out[C_ST] == "Reconciled").sum())
print(f"formatted Excel + csv → {vroot}/output/  ·  {recon}/{len(out)} reconciled, {len(out)-recon} exception(s)")
display(spark.table(f"{fqn}.cf_cashflow_rec"))
