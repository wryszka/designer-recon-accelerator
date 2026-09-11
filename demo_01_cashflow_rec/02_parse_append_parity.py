# Databricks notebook source
# MAGIC %md
# MAGIC # UC1 · Parse → append → parity → formatted Excel
# MAGIC
# MAGIC The coded reference for the cash-flow rec — what the **Lakeflow Designer** canvas reproduces
# MAGIC visually. It:
# MAGIC 1. **reads the header cells** from each account's bank-rec workbook (and the 2-cell fallback
# MAGIC    for accounts whose workbook is missing),
# MAGIC 2. derives this period's **Current** (bank position) and **Control** (SAP − Bank) values,
# MAGIC 3. **appends the two new columns** onto the rolling cash-flow file — by *name*, so the moving-
# MAGIC    column-position problem that plagued the desktop-ETL build simply doesn't arise,
# MAGIC 4. proves the result matches the benchmark **to the penny** (`cf_benchmark`),
# MAGIC 5. writes a **formatted Excel** output — no template + Format-Painter dance.
# MAGIC
# MAGIC In the demo the Designer canvas replaces steps 1–3 and writes its own output table; `02` then
# MAGIC checks that table against `cf_benchmark`. Here we do it in code so the parity is provable.

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

import os, glob, shutil
import pandas as pd
from openpyxl import load_workbook

cur_label = pd.Period(period, freq="M").strftime("%b")
C_CUR, C_CTL = f"{cur_label}_Current", f"{cur_label}_Control"

# COMMAND ----------

# ---- 1. parse the header cells from each bank-rec workbook --------------------------
def read_header(path):
    ws = load_workbook(path, data_only=True)["Header"]
    vals = {}
    for r in range(2, 6):                                   # rows 2..5 = SAP/Accurate/Bank/Control
        k, v = ws[f"A{r}"].value, ws[f"B{r}"].value
        if k is not None:
            vals[str(k)] = v
    return vals

rows = []
for path in sorted(glob.glob(f"{vroot}/bank_recs/BankRec_*_{period}.xlsx")):
    code = os.path.basename(path).replace("BankRec_", "").replace(f"_{period}.xlsx", "")
    h = read_header(path)
    rows.append({"account_code": code, "current_period": round(float(h["Bank"]), 2),
                 "period_control": round(float(h["SAP"]) - float(h["Bank"]), 2), "source": "bank_rec"})

# ---- 2. fallback: 2 cells (SAP + Bank) for accounts with no workbook ----------------
sap_fb = {os.path.basename(p).replace("SAP_", "").replace(f"_{period}.csv", ""): pd.read_csv(p)["SAP"][0]
          for p in glob.glob(f"{vroot}/sap_fallback/SAP_*_{period}.csv")}
bank_fb = {os.path.basename(p).replace("Bank_", "").replace(f"_{period}.csv", ""): pd.read_csv(p)["Bank"][0]
           for p in glob.glob(f"{vroot}/bank_fallback/Bank_*_{period}.csv")}
for code in sorted(sap_fb):
    rows.append({"account_code": code, "current_period": round(float(bank_fb[code]), 2),
                 "period_control": round(float(sap_fb[code]) - float(bank_fb[code]), 2), "source": "fallback"})

extract = pd.DataFrame(rows).sort_values("account_code").reset_index(drop=True)
print(f"parsed {len(extract)} accounts "
      f"({(extract.source=='bank_rec').sum()} workbook, {(extract.source=='fallback').sum()} fallback)")

# COMMAND ----------

# ---- 3. append the two new columns onto the rolling file ----------------------------
prior_path = sorted(glob.glob(f"{vroot}/prior/CashFlowRec_*.xlsx"))[-1]
rolling = pd.read_excel(prior_path, sheet_name="CashFlowRec")
produced = rolling.merge(extract[["account_code", "current_period", "period_control"]], on="account_code", how="left")
produced = produced.rename(columns={"current_period": C_CUR, "period_control": C_CTL})

spark.createDataFrame(produced).write.mode("overwrite").option("overwriteSchema", "true").saveAsTable(f"{fqn}.cf_cashflow_rec")
spark.sql(f"COMMENT ON TABLE {fqn}.cf_cashflow_rec IS 'UC1 produced rolling cash-flow rec (prior + the two new period columns). Synthetic.'")

# COMMAND ----------

# ---- 4. parity vs the benchmark, to the penny ---------------------------------------
bench = spark.table(f"{fqn}.cf_benchmark").toPandas()
common = [c for c in bench.columns if c in produced.columns]
p = produced[common].sort_values("account_code").reset_index(drop=True)
b = bench[common].sort_values("account_code").reset_index(drop=True)

num = [c for c in common if c not in ("account_code", "account_name")]
p[num] = p[num].round(2); b[num] = b[num].round(2)
diffs = (p[num] - b[num]).abs()
mismatch = int((diffs > 0.005).sum().sum())
print(f"PARITY: {'✅ to the penny' if mismatch == 0 else f'❌ {mismatch} cell(s) differ'} "
      f"across {len(p)} accounts × {len(num)} value columns")
assert mismatch == 0, "parity failed — canvas/coded output does not match benchmark"

# COMMAND ----------

# ---- 5. formatted Excel output (no template + Format-Painter) ------------------------
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

out = produced.copy()
wb = __import__("openpyxl").Workbook()
ws = wb.active; ws.title = f"CashFlowRec {period}"
hdr_fill = PatternFill("solid", fgColor="1B3A4B"); hdr_font = Font(bold=True, color="FFFFFF")
thin = Side(style="thin", color="D9D9D9"); border = Border(*(thin,) * 4)
ctrl_cols = {c for c in out.columns if c.endswith("_Control")}

ws.append(list(out.columns))
for j, c in enumerate(out.columns, 1):
    cell = ws.cell(row=1, column=j); cell.fill = hdr_fill; cell.font = hdr_font
    cell.alignment = Alignment(horizontal="center"); cell.border = border
for _, r in out.iterrows():
    ws.append([r[c] for c in out.columns])
for i in range(2, ws.max_row + 1):
    for j, c in enumerate(out.columns, 1):
        cell = ws.cell(row=i, column=j); cell.border = border
        if c not in ("account_code", "account_name"):
            cell.number_format = "#,##0.00"
            if c in ctrl_cols and isinstance(cell.value, (int, float)) and abs(cell.value) > 0.005:
                cell.font = Font(color="C00000", bold=True)     # highlight control breaks
for j, c in enumerate(out.columns, 1):
    ws.column_dimensions[get_column_letter(j)].width = 22 if c == "account_name" else 14
ws.freeze_panes = "C2"

tmp = f"/tmp/CashFlowRec_{period}.xlsx"; wb.save(tmp)
os.makedirs(f"{vroot}/output", exist_ok=True)
shutil.copy(tmp, f"{vroot}/output/CashFlowRec_{period}.xlsx")
print(f"formatted Excel → {vroot}/output/CashFlowRec_{period}.xlsx")
display(spark.table(f"{fqn}.cf_cashflow_rec"))
