# Databricks notebook source
# MAGIC %md
# MAGIC # UC1 · the receipt behind the Designer flow (NOT shown in the room)
# MAGIC
# MAGIC This is the **coded mirror** of the no-code **Lakeflow Designer** flow. It is **not** part of what a
# MAGIC customer builds or maintains — it exists so *we* can prove the visual flow ties out. In the room the
# MAGIC **Designer canvas** does the reconciliation (steps 1–3) with **no code**, and the analyst gets the
# MAGIC Excel from a **standard download** — nobody writes or maintains this.
# MAGIC 1. join the rolling file (`cf_prior_rec`) to this month's numbers (`cf_period_extract`) on `account_code`,
# MAGIC 2. derive **`Jul_Status`** = *Reconciled* when Control nets to 0, else *Exception*,
# MAGIC 3. append **`Jul_Current`** / **`Jul_Control`**  — *(1–3 = exactly what the Designer canvas produces)*,
# MAGIC 4. **demo-only QA:** check it matches the synthetic benchmark to the penny (there is **no benchmark**
# MAGIC    in a real deployment — this is scaffolding to prove our demo, never presented),
# MAGIC 5. **standard export:** drop plain `.csv` + `.xlsx` into the folder — stock save, **no formatting code**.

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

# ---- 4. DEMO-ONLY QA: parity vs the synthetic benchmark (no benchmark exists in production) ----
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

# ---- 5. standard export — stock CSV + Excel, NO formatting code to write or maintain ----
# This is a plain "save as CSV / save as Excel", the same download any table gives you — not hand-styled
# Python. In the room the analyst just downloads the Designer flow's output; here we drop both file types
# into the folder as examples. Exception highlighting lives in the dashboard/Genie layer, not in code here.
os.makedirs(f"{vroot}/output", exist_ok=True)
out.to_csv(f"{vroot}/output/CashFlowRec_{period}.csv", index=False)
# stock to_excel, no styling; write local first then copy (Volumes FUSE has no random-access write for xlsx)
_t = tempfile.mkdtemp(); out.to_excel(f"{_t}/o.xlsx", index=False); shutil.copy(f"{_t}/o.xlsx", f"{vroot}/output/CashFlowRec_{period}.xlsx")

recon = int((out[C_ST] == "Reconciled").sum())
print(f"CSV + Excel → {vroot}/output/  ·  {recon}/{len(out)} reconciled, {len(out)-recon} exception(s)")
display(spark.table(f"{fqn}.cf_cashflow_rec"))
