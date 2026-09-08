# Databricks notebook source
# MAGIC %md
# MAGIC # UC1 · Cash matching — generate the sources
# MAGIC
# MAGIC A period-end **bank reconciliation** across many accounts, pulled from three systems:
# MAGIC a general-ledger (ERP) export, a bank-statement feed, and the prior-period
# MAGIC reconciliation baseline. Each account must reconcile: the GL closing balance equals
# MAGIC the bank closing balance once timing (outstanding) items are accounted for — i.e. it
# MAGIC **nets to zero**. A handful of accounts carry a residual variance — those are the
# MAGIC exceptions an auditor cares about.
# MAGIC
# MAGIC Everything is synthetic and prefixed `cm_`. No real organisation, bank or account.
# MAGIC
# MAGIC | Table | What it is |
# MAGIC |---|---|
# MAGIC | `cm_accounts` | account reference: code, name, GL account, house bank, currency |
# MAGIC | `cm_gl_balances` | current-period balances from the ledger/ERP + outstanding-in-GL items |
# MAGIC | `cm_bank_balances` | current-period balances from the bank feed + outstanding-on-bank items |
# MAGIC | `cm_prior_recon` | prior-period closing balances (the opening baseline) |
# MAGIC | `cm_benchmark` | the reconciliation the coded pipeline produces — `02_parity` proves the canvas matches |

# COMMAND ----------

dbutils.widgets.text("catalog_name", "lr_dev_aws_us_catalog")
dbutils.widgets.text("schema_name", "designer_recon_demo")
dbutils.widgets.text("period", "2026-07")
dbutils.widgets.text("seed", "71")
catalog = dbutils.widgets.get("catalog_name")
schema = dbutils.widgets.get("schema_name")
period = dbutils.widgets.get("period")
seed = int(dbutils.widgets.get("seed"))
fqn = f"{catalog}.{schema}"

spark.sql(f"CREATE SCHEMA IF NOT EXISTS {fqn}")

# COMMAND ----------

import numpy as np, pandas as pd
rng = np.random.default_rng(seed)
prior_period = (pd.Period(period, freq="M") - 1).strftime("%Y-%m")

N = 44                                   # number of bank accounts
CCY = ["GBP", "GBP", "GBP", "EUR", "USD", "CAD"]   # GBP-weighted
HOUSE_BANKS = ["HB01", "HB02", "HB03", "HB04"]

acc = []
for i in range(1, N + 1):
    code = f"ACC-{i:03d}"
    acc.append((code, f"Operating account {i:03d}", f"GL{10000 + i}",
                HOUSE_BANKS[i % len(HOUSE_BANKS)], CCY[i % len(CCY)]))
accounts = pd.DataFrame(acc, columns=["account_code", "account_name", "gl_account", "house_bank", "currency"])

# prior-period closing = this period opening
prior_close = np.round(rng.uniform(50_000, 5_000_000, N), 2)
prior = pd.DataFrame({"account_code": accounts.account_code, "period": prior_period,
                      "closing_balance_gl": prior_close, "closing_balance_bank": prior_close})

# current period: movements, and timing (outstanding) items
movement = np.round(rng.normal(0, 250_000, N), 2)
gl_close = np.round(prior_close + movement, 2)
os_bank_not_gl = np.round(np.where(rng.random(N) < 0.5, rng.uniform(0, 40_000, N), 0), 2)   # on bank, not yet in GL
os_gl_not_bank = np.round(np.where(rng.random(N) < 0.4, rng.uniform(0, 25_000, N), 0), 2)   # in GL, not yet on bank
# bank closing derived so that GL = Bank + (os_bank_not_gl) - (os_gl_not_bank)  → variance 0
bank_close = np.round(gl_close - os_bank_not_gl + os_gl_not_bank, 2)

# inject a few genuine exceptions (residual variance) — the audit findings
exceptions = rng.choice(N, size=3, replace=False)
bank_close[exceptions] = np.round(bank_close[exceptions] + rng.uniform(150, 900, 3) * rng.choice([-1, 1], 3), 2)

gl = pd.DataFrame({"account_code": accounts.account_code, "period": period,
                   "opening_balance_gl": prior_close, "closing_balance_gl": gl_close,
                   "os_gl_not_bank": os_gl_not_bank})
bank = pd.DataFrame({"account_code": accounts.account_code, "period": period,
                     "opening_balance_bank": prior_close, "closing_balance_bank": bank_close,
                     "os_bank_not_gl": os_bank_not_gl})

# the coded reconciliation (parity oracle)
variance = np.round(gl_close - (bank_close + os_bank_not_gl - os_gl_not_bank), 2)
benchmark = pd.DataFrame({
    "account_code": accounts.account_code, "period": period,
    "closing_balance_gl": gl_close, "closing_balance_bank": bank_close,
    "os_bank_not_gl": os_bank_not_gl, "os_gl_not_bank": os_gl_not_bank,
    "variance": variance,
    "status": np.where(np.abs(variance) < 0.01, "Reconciled", "Exception"),
})

# COMMAND ----------

def write(df, name, comment):
    spark.createDataFrame(df).write.mode("overwrite").option("overwriteSchema", "true").saveAsTable(f"{fqn}.{name}")
    spark.sql(f"COMMENT ON TABLE {fqn}.{name} IS '{comment}'")

write(accounts, "cm_accounts", "Bank account reference (synthetic). code / name / GL account / house bank / currency.")
write(gl, "cm_gl_balances", "Current-period ledger/ERP balances + outstanding-in-GL items (synthetic).")
write(bank, "cm_bank_balances", "Current-period bank-feed balances + outstanding-on-bank items (synthetic).")
write(prior, "cm_prior_recon", "Prior-period closing balances = current opening baseline (synthetic).")
write(benchmark, "cm_benchmark", "Coded reconciliation: variance per account + Reconciled/Exception. Parity oracle for the Designer canvas. Synthetic.")

print(f"{N} accounts · {int((benchmark.status=='Exception').sum())} exceptions injected")
display(spark.sql(f"SELECT status, count(*) accounts, round(sum(abs(variance)),2) total_abs_variance FROM {fqn}.cm_benchmark GROUP BY status"))
