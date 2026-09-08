# Databricks notebook source
# MAGIC %md
# MAGIC # UC2 · Control sheet — generate the sources
# MAGIC
# MAGIC A payments dataset is split into several **branches** (by company, category and bank),
# MAGIC each summarised on a control sheet — and every branch must tie back to the main total
# MAGIC with **zero variance**. It's the classic "prove the parts equal the whole" control.
# MAGIC
# MAGIC Everything is synthetic and prefixed `cs_`. Suppliers, companies and banks are generic
# MAGIC placeholders — no real organisation or payee.
# MAGIC
# MAGIC | Table | What it is |
# MAGIC |---|---|
# MAGIC | `cs_payments` | payment transactions (the main dataset) |
# MAGIC | `cs_category_lookup` | supplier → category (the VLOOKUP join) |
# MAGIC | `cs_benchmark` | the control sheet the coded pipeline produces (per-branch totals + main + variance) |

# COMMAND ----------

dbutils.widgets.text("catalog_name", "lr_dev_aws_us_catalog")
dbutils.widgets.text("schema_name", "designer_recon_demo")
dbutils.widgets.text("n_payments", "6000")
dbutils.widgets.text("seed", "72")
catalog = dbutils.widgets.get("catalog_name")
schema = dbutils.widgets.get("schema_name")
n = int(dbutils.widgets.get("n_payments"))
seed = int(dbutils.widgets.get("seed"))
fqn = f"{catalog}.{schema}"
spark.sql(f"CREATE SCHEMA IF NOT EXISTS {fqn}")

# COMMAND ----------

import numpy as np, pandas as pd
rng = np.random.default_rng(seed)

CATEGORIES = ["Claims", "Refund", "Cashback", "Uncashed", "Promise", "Travel"]
COMPANY_CODES = ["CC01", "CC02"]
HOUSE_BANKS = ["HB01", "HB02", "HB03"]
PAYMENT_METHODS = ["Cheque", "BACS", "FasterPayment"]

# supplier → category lookup
n_suppliers = 60
suppliers = [f"SUP-{i:04d}" for i in range(1, n_suppliers + 1)]
lookup = pd.DataFrame({"supplier": suppliers,
                       "category": rng.choice(CATEGORIES, size=n_suppliers)})

# payments (the main dataset)
sup = rng.choice(suppliers, size=n)
pay = pd.DataFrame({
    "payment_doc_no": np.arange(1900000000, 1900000000 + n),
    "payment_date": pd.to_datetime("2026-06-01") + pd.to_timedelta(rng.integers(0, 90, n), unit="D"),
    "currency": "GBP",
    "amount_paid": -np.round(rng.gamma(2.0, 400, n), 2),          # outflows (negative)
    "supplier": sup,
    "company_code": rng.choice(COMPANY_CODES, size=n, p=[0.6, 0.4]),
    "account_id": rng.integers(1888000000, 1888000100, n),
    "house_bank": rng.choice(HOUSE_BANKS, size=n),
    "payment_method": rng.choice(PAYMENT_METHODS, size=n),
    "payee_name": [f"Payee {s[-4:]}" for s in sup],
})
pay["payment_date"] = pay["payment_date"].dt.date.astype(str)

# the branch key: a clean partition of every row into 6 branches, so the parts sum to the whole.
cat_of = dict(zip(lookup.supplier, lookup.category))
pay["category"] = pay["supplier"].map(cat_of)
provider = np.where(pay["category"].isin(["Claims", "Refund", "Travel"]), "Provider", "NonProvider")
img = np.where((pay["account_id"] % 2) == 0, "Img2", "Img3")
pay["branch"] = pay["company_code"] + " " + provider + " " + img

# coded control sheet (parity oracle): per-branch total + main total + variance
branch_tot = pay.groupby("branch", as_index=False)["amount_paid"].sum().round(2)
branch_tot.columns = ["branch", "branch_total"]
main_total = round(pay["amount_paid"].sum(), 2)
branch_tot["variance"] = 0.00
summary = pd.concat([
    branch_tot,
    pd.DataFrame([{"branch": "MAIN (all payments)", "branch_total": main_total,
                   "variance": round(branch_tot["branch_total"].sum() - main_total, 2)}]),
], ignore_index=True)

# COMMAND ----------

def write(df, name, comment):
    spark.createDataFrame(df).write.mode("overwrite").option("overwriteSchema", "true").saveAsTable(f"{fqn}.{name}")
    spark.sql(f"COMMENT ON TABLE {fqn}.{name} IS '{comment}'")

write(pay.drop(columns=["category", "branch"]), "cs_payments", "Payment transactions, the main dataset (synthetic). Split into branches downstream.")
write(lookup, "cs_category_lookup", "Supplier → category lookup — the VLOOKUP join (synthetic).")
write(summary, "cs_benchmark", "Coded control sheet: per-branch totals + MAIN total + variance (0.00). Parity oracle for the Designer canvas. Synthetic.")

print(f"{n:,} payments · main total {main_total:,.2f} · {branch_tot.shape[0]} branches")
display(spark.sql(f"SELECT * FROM {fqn}.cs_benchmark ORDER BY branch"))
