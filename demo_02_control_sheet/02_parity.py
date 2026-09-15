# Databricks notebook source
# MAGIC %md
# MAGIC # UC2 · Build the control sheet + parity + formatted Excel
# MAGIC
# MAGIC The coded mirror of the **Lakeflow Designer** flow, so we can prove it ties out:
# MAGIC 1. join `cs_payments` to `cs_category_lookup` on `supplier` (the VLOOKUP),
# MAGIC 2. derive the **branch** group (the "six or seven tables"),
# MAGIC 3. **aggregate** each branch total,
# MAGIC 4. add the **MAIN (all payments)** total + a `variance`,
# MAGIC 5. prove the parts **tie back to the whole with 0.00 variance** (vs `cs_benchmark`),
# MAGIC 6. write a **formatted Excel** (`.xlsx` + `.csv`).
# MAGIC
# MAGIC In the room the Designer canvas does 1–4 with no code; this notebook is the receipt.

# COMMAND ----------

# MAGIC %pip install openpyxl -q
# MAGIC dbutils.library.restartPython()

# COMMAND ----------

dbutils.widgets.text("catalog_name", "lr_dev_aws_us_catalog")
dbutils.widgets.text("schema_name", "designer_recon_demo")
dbutils.widgets.text("landing_volume_name", "recon_landing")
catalog = dbutils.widgets.get("catalog_name"); schema = dbutils.widgets.get("schema_name")
volume = dbutils.widgets.get("landing_volume_name")
fqn = f"{catalog}.{schema}"
vroot = f"/Volumes/{catalog}/{schema}/{volume}/uc2"

import os, shutil, tempfile
import numpy as np, pandas as pd

# COMMAND ----------

# ---- 1-4. join → branch → aggregate → MAIN (what the Designer canvas produces) ----
pay = spark.table(f"{fqn}.cs_payments").toPandas()
lookup = spark.table(f"{fqn}.cs_category_lookup").toPandas()

j = pay.merge(lookup, on="supplier", how="inner")                       # 1. VLOOKUP
provider = np.where(j["category"].isin(["Claims", "Refund", "Travel"]), "Provider", "NonProvider")
img = np.where((j["account_id"] % 2) == 0, "Img2", "Img3")
j["branch"] = j["company_code"] + " " + provider + " " + img            # 2. branch group

bt = j.groupby("branch", as_index=False)["amount_paid"].sum().round(2)   # 3. aggregate each branch
bt.columns = ["branch", "branch_total"]; bt["variance"] = 0.00
main_total = round(j["amount_paid"].sum(), 2)
control = pd.concat([bt, pd.DataFrame([{"branch": "MAIN (all payments)", "branch_total": main_total,
                                        "variance": round(bt["branch_total"].sum() - main_total, 2)}])],
                    ignore_index=True)                                   # 4. MAIN total + variance

spark.createDataFrame(control).write.mode("overwrite").option("overwriteSchema", "true").saveAsTable(f"{fqn}.cs_control_sheet")
spark.sql(f"COMMENT ON TABLE {fqn}.cs_control_sheet IS 'UC2 produced control sheet: per-branch totals + MAIN + variance. Synthetic.'")

# COMMAND ----------

# ---- 5. parity: matches the oracle AND the parts tie to the whole (0.00) ----
bench = spark.table(f"{fqn}.cs_benchmark").toPandas().sort_values("branch").reset_index(drop=True)
got = control.sort_values("branch").reset_index(drop=True)
mism = int((got.set_index("branch")["branch_total"].round(2) - bench.set_index("branch")["branch_total"].round(2)).abs().gt(0.005).sum())
parts = round(bt["branch_total"].sum(), 2)
tie = round(parts - main_total, 2)
print(f"PARITY: {'✅ matches oracle' if mism == 0 else f'❌ {mism} branch diffs'} · parts {parts:,.2f} vs whole {main_total:,.2f} → variance {tie:.2f}")
assert mism == 0 and abs(tie) < 0.01, "parity failed"

# COMMAND ----------

# ---- 6. formatted Excel (+ csv) out ----
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

out = control.copy()
wb = Workbook(); ws = wb.active; ws.title = "Control sheet"
hdr = PatternFill("solid", fgColor="1B3A4B"); hf = Font(bold=True, color="FFFFFF")
thin = Side(style="thin", color="D9D9D9"); bd = Border(thin, thin, thin, thin)
ws.append(list(out.columns))
for j2, c in enumerate(out.columns, 1):
    cell = ws.cell(1, j2); cell.fill = hdr; cell.font = hf; cell.alignment = Alignment(horizontal="center"); cell.border = bd
for _, r in out.iterrows():
    ws.append([r[c] for c in out.columns])
for i in range(2, ws.max_row + 1):
    for j2, c in enumerate(out.columns, 1):
        cell = ws.cell(i, j2); cell.border = bd
        if c in ("branch_total", "variance"):
            cell.number_format = "#,##0.00"
        if ws.cell(i, 1).value == "MAIN (all payments)":
            cell.font = Font(bold=True)                                  # highlight the MAIN total row
for j2, c in enumerate(out.columns, 1):
    ws.column_dimensions[get_column_letter(j2)].width = 24 if c == "branch" else 16
ws.freeze_panes = "A2"
_t = tempfile.mkdtemp(); wb.save(f"{_t}/cs.xlsx")
os.makedirs(f"{vroot}/output", exist_ok=True)
shutil.copy(f"{_t}/cs.xlsx", f"{vroot}/output/ControlSheet.xlsx")
out.to_csv(f"{vroot}/output/ControlSheet.csv", index=False)
print(f"formatted Excel + csv → {vroot}/output/  ·  {len(bt)} branches tie to the whole, variance {tie:.2f}")
display(spark.table(f"{fqn}.cs_control_sheet"))
