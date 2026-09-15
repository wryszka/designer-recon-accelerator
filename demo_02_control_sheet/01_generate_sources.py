# Databricks notebook source
# MAGIC %md
# MAGIC # UC2 · Control sheet — generate the sources (kept small & legible)
# MAGIC
# MAGIC Two datasets: a **payments** sheet and a **supplier → category** lookup. Join them, split into
# MAGIC **branch groups** (the "six or seven tables"), and a **control sheet** sums each — and the parts
# MAGIC must **tie back to the whole with 0.00 variance**.
# MAGIC
# MAGIC Kept deliberately small (~400 payments) so the output control sheet is a handful of legible rows.
# MAGIC Everything synthetic, prefixed `cs_`. Inputs land as **xlsx + csv** in `uc2/inputs/` (droppable
# MAGIC into Designer); tables are also registered.
# MAGIC
# MAGIC | Table | What it is |
# MAGIC |---|---|
# MAGIC | `cs_payments` | payment transactions (the main dataset) |
# MAGIC | `cs_category_lookup` | supplier → category (the VLOOKUP join) |
# MAGIC | `cs_benchmark` | the control sheet the coded pipeline produces (per-branch totals + MAIN + variance) |

# COMMAND ----------

# MAGIC %pip install openpyxl -q
# MAGIC dbutils.library.restartPython()

# COMMAND ----------

dbutils.widgets.text("catalog_name", "lr_dev_aws_us_catalog")
dbutils.widgets.text("schema_name", "designer_recon_demo")
dbutils.widgets.text("landing_volume_name", "recon_landing")
dbutils.widgets.text("n_payments", "400")
dbutils.widgets.text("seed", "72")
catalog = dbutils.widgets.get("catalog_name"); schema = dbutils.widgets.get("schema_name")
volume = dbutils.widgets.get("landing_volume_name")
n = int(dbutils.widgets.get("n_payments")); seed = int(dbutils.widgets.get("seed"))
fqn = f"{catalog}.{schema}"
spark.sql(f"CREATE SCHEMA IF NOT EXISTS {fqn}")
spark.sql(f"CREATE VOLUME IF NOT EXISTS {fqn}.{volume}")

import os, shutil, tempfile
import numpy as np, pandas as pd
rng = np.random.default_rng(seed)
TMP = tempfile.mkdtemp()
vroot = f"/Volumes/{catalog}/{schema}/{volume}/uc2"
shutil.rmtree(vroot, ignore_errors=True)
for d in ["inputs", "output"]:
    os.makedirs(f"{vroot}/{d}", exist_ok=True)

# COMMAND ----------

CATEGORIES = ["Claims", "Refund", "Cashback", "Uncashed", "Promise", "Travel"]
COMPANY_CODES = ["CC01", "CC02"]
HOUSE_BANKS = ["HB01", "HB02", "HB03"]
PAYMENT_METHODS = ["Cheque", "BACS", "FasterPayment"]

n_suppliers = 30
suppliers = [f"SUP-{i:04d}" for i in range(1, n_suppliers + 1)]
lookup = pd.DataFrame({"supplier": suppliers, "category": rng.choice(CATEGORIES, size=n_suppliers)})

sup = rng.choice(suppliers, size=n).astype(object)
sup[rng.choice(n, size=8, replace=False)] = "SUP-9999"             # a supplier NOT in the lookup → must show as an Unmatched group, never silently dropped
pay = pd.DataFrame({
    "payment_doc_no": np.arange(1900000000, 1900000000 + n),
    "payment_date": (pd.to_datetime("2026-06-01") + pd.to_timedelta(rng.integers(0, 90, n), unit="D")).astype(str).str.slice(0, 10),
    "currency": "GBP",
    "amount_paid": -np.round(rng.gamma(2.0, 400, n), 2),           # outflows (negative)
    "supplier": sup,
    "company_code": rng.choice(COMPANY_CODES, size=n, p=[0.6, 0.4]),
    "account_id": rng.integers(1888000000, 1888000100, n),
    "house_bank": rng.choice(HOUSE_BANKS, size=n),
    "payment_method": rng.choice(PAYMENT_METHODS, size=n),
    "payee_name": [f"Payee {str(s)[-4:]}" for s in sup],
})

# branch = company + provider-flag + image group; unmatched suppliers get their OWN visible group
cat_of = dict(zip(lookup.supplier, lookup.category))
cat = pd.Series(sup).map(cat_of)                                   # NaN where supplier not in the lookup
provider = np.where(cat.isin(["Claims", "Refund", "Travel"]), "Provider", "NonProvider")
img = np.where((pay["account_id"] % 2) == 0, "Img2", "Img3")
branch = np.where(cat.isna(), "Unmatched (no category)", pay["company_code"] + " " + provider + " " + img)

branch_tot = pay.assign(branch=branch).groupby("branch", as_index=False)["amount_paid"].sum().round(2)
branch_tot.columns = ["branch", "branch_total"]; branch_tot["variance"] = 0.00
main_total = round(pay["amount_paid"].sum(), 2)
benchmark = pd.concat([branch_tot,
    pd.DataFrame([{"branch": "MAIN (all payments)", "branch_total": main_total,
                   "variance": round(branch_tot["branch_total"].sum() - main_total, 2)}])], ignore_index=True)

# COMMAND ----------

# ---- land the two input datasets as xlsx + csv (droppable into Designer) ----
def land(df, name):
    df.to_excel(f"{TMP}/{name}.xlsx", index=False, sheet_name="Sheet1"); shutil.copy(f"{TMP}/{name}.xlsx", f"{vroot}/inputs/{name}.xlsx")
    df.to_csv(f"{vroot}/inputs/{name}.csv", index=False)

land(pay, "Payments")
land(lookup, "CategoryLookup")

def write(df, name, comment):
    spark.createDataFrame(df).write.mode("overwrite").option("overwriteSchema", "true").saveAsTable(f"{fqn}.{name}")
    spark.sql(f"COMMENT ON TABLE {fqn}.{name} IS '{comment}'")

write(pay, "cs_payments", "UC2 payment transactions, the main dataset (synthetic).")
write(lookup, "cs_category_lookup", "UC2 supplier to category lookup — the VLOOKUP join (synthetic).")
write(benchmark, "cs_benchmark", "UC2 coded control sheet: per-branch totals + MAIN + variance 0.00. Parity oracle. Synthetic.")

print(f"{n} payments · {branch_tot.shape[0]} branches · MAIN total {main_total:,.2f}")
print("inputs:", os.listdir(f"{vroot}/inputs"))
display(spark.table(f"{fqn}.cs_benchmark"))
