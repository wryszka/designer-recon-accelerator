# Databricks notebook source
# MAGIC %md
# MAGIC # UC2 · the receipt behind the Designer flow (NOT shown in the room)
# MAGIC
# MAGIC The **coded mirror** of the no-code **Lakeflow Designer** flow — **not** what a customer builds or
# MAGIC maintains. In the room the **Designer canvas** does the join / branch / aggregate with **no code**, the
# MAGIC reconciliation shows as a **results table**, and the Excel comes from a **standard download**.
# MAGIC 1. join `cs_payments` to `cs_category_lookup` on `supplier` — **LEFT join, so no payment is dropped**,
# MAGIC 2. derive the **branch** group; a supplier not in the lookup gets its **own Unmatched group**,
# MAGIC 3. **aggregate** each group total,
# MAGIC 4. **population reconciliation** — prove **rows in = rows grouped** (0 dropped), **0 duplicate
# MAGIC    suppliers** (0 fan-out), **Σ groups = Σ all payments** (the true whole). Shown as the table
# MAGIC    `cs_population_recon`, **not as code**. *(The benchmark comparison is demo-only QA — no benchmark in production.)*
# MAGIC 5. **formatted export (hidden setup, never shown):** a small set-once template (bold header, number
# MAGIC    format, Unmatched in red, MAIN in bold) — reused, not bespoke per-rec code.
# MAGIC
# MAGIC "Parts tie to the whole" only means something once you've proven the whole is *every* payment.

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

# ---- 1-3. LEFT join → branch (Unmatched keeps its own group) → aggregate ----
pay = spark.table(f"{fqn}.cs_payments").toPandas()
lookup = spark.table(f"{fqn}.cs_category_lookup").toPandas()

dup_suppliers = int(lookup["supplier"].duplicated().sum())          # >0 would fan-out (double-count) — guard below
j = pay.merge(lookup, on="supplier", how="left")                    # LEFT — every payment kept, nothing silently dropped
provider = np.where(j["category"].isin(["Claims", "Refund", "Travel"]), "Provider", "NonProvider")
img = np.where((j["account_id"] % 2) == 0, "Img2", "Img3")
j["branch"] = np.where(j["category"].isna(), "Unmatched (no category)", j["company_code"] + " " + provider + " " + img)

bt = j.groupby("branch", as_index=False)["amount_paid"].sum().round(2)
bt.columns = ["branch", "branch_total"]; bt["variance"] = 0.00
main_total = round(j["amount_paid"].sum(), 2)
control = pd.concat([bt, pd.DataFrame([{"branch": "MAIN (all payments)", "branch_total": main_total,
                                        "variance": round(bt["branch_total"].sum() - main_total, 2)}])], ignore_index=True)
spark.createDataFrame(control).write.mode("overwrite").option("overwriteSchema", "true").saveAsTable(f"{fqn}.cs_control_sheet")
spark.sql(f"COMMENT ON TABLE {fqn}.cs_control_sheet IS 'UC2 control sheet: per-branch totals (incl Unmatched) + MAIN. Synthetic.'")

# COMMAND ----------

# ---- 4. population reconciliation — the real correctness check ----
rows_in = len(pay)
rows_unmatched = int(j["category"].isna().sum())
rows_matched = rows_in - rows_unmatched
sum_all = round(pay["amount_paid"].sum(), 2)
sum_groups = round(bt["branch_total"].sum(), 2)
tie = round(sum_groups - sum_all, 2)

bench = spark.table(f"{fqn}.cs_benchmark").toPandas().set_index("branch")["branch_total"].round(2)
got = control.set_index("branch")["branch_total"].round(2)
mism = int((got - bench).abs().gt(0.005).sum())

recon = pd.DataFrame([{"rows_in": rows_in, "rows_matched": rows_matched, "rows_unmatched": rows_unmatched,
                       "rows_after_join": len(j), "dup_suppliers_in_lookup": dup_suppliers,
                       "sum_all_payments": sum_all, "sum_of_groups": sum_groups, "variance": tie}])
spark.createDataFrame(recon).write.mode("overwrite").option("overwriteSchema", "true").saveAsTable(f"{fqn}.cs_population_recon")
spark.sql(f"COMMENT ON TABLE {fqn}.cs_population_recon IS 'UC2 population reconciliation: every payment accounted for (matched+unmatched=total, no fan-out), groups sum to all. Synthetic.'")

ok = (mism == 0 and abs(tie) < 0.01 and dup_suppliers == 0 and len(j) == rows_in and rows_matched + rows_unmatched == rows_in)
print(f"PARITY {'✅' if mism==0 else '❌'} vs oracle · POPULATION: {rows_in} in = {rows_matched} matched + {rows_unmatched} unmatched · "
      f"rows_after_join {len(j)} (no fan-out) · dup suppliers {dup_suppliers} · Σgroups {sum_groups:,.2f} = Σall {sum_all:,.2f} (variance {tie:.2f})")
assert ok, "UC2 correctness check failed"

# COMMAND ----------

# ---- 5. formatted Excel out — a small reusable export template (HIDDEN setup; never shown in the room) ----
# Bold header + number format + Unmatched in red + MAIN in bold. Set-once, reused (not bespoke per-rec
# code), never on the demo surface. Local write then copy (Volumes FUSE has no random-access xlsx write).
from openpyxl.styles import Font, PatternFill
out = control.copy()
os.makedirs(f"{vroot}/output", exist_ok=True)
out.to_csv(f"{vroot}/output/ControlSheet.csv", index=False)
_t = tempfile.mkdtemp(); xpath = f"{_t}/cs.xlsx"
with pd.ExcelWriter(xpath, engine="openpyxl") as xw:
    out.to_excel(xw, index=False, sheet_name="Control sheet")
    ws = xw.sheets["Control sheet"]
    for cell in ws[1]:
        cell.font = Font(bold=True, color="FFFFFF"); cell.fill = PatternFill("solid", fgColor="1B3A4B")
    num_cols = [i + 1 for i, c in enumerate(out.columns) if c in ("branch_total", "variance")]
    for r in range(2, ws.max_row + 1):
        for i in num_cols:
            ws.cell(r, i).number_format = "#,##0.00"
        label = ws.cell(r, 1).value
        if label == "MAIN (all payments)":
            for c in range(1, ws.max_column + 1):
                ws.cell(r, c).font = Font(bold=True)
        elif label == "Unmatched (no category)":
            for c in range(1, ws.max_column + 1):
                ws.cell(r, c).font = Font(color="C00000")
shutil.copy(xpath, f"{vroot}/output/ControlSheet.xlsx")
print(f"CSV + formatted Excel → {vroot}/output/")
display(spark.table(f"{fqn}.cs_population_recon"))
