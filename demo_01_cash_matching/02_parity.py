# Databricks notebook source
# MAGIC %md
# MAGIC # UC1 · Prove the canvas matches the coded reconciliation
# MAGIC
# MAGIC You built `cm_reconciliation` on the Lakeflow Designer canvas (see `README.md`). This
# MAGIC compares it, account for account, to `cm_benchmark` — the same reconciliation produced
# MAGIC by hand-written code — including which accounts are flagged as **Exception**. If every
# MAGIC account matches, the no-code canvas and the coded pipeline agree to the penny.

# COMMAND ----------

dbutils.widgets.text("catalog_name", "lr_dev_aws_us_catalog")
dbutils.widgets.text("schema_name", "designer_recon_demo")
dbutils.widgets.text("canvas_output", "cm_reconciliation")
catalog = dbutils.widgets.get("catalog_name")
schema = dbutils.widgets.get("schema_name")
canvas = dbutils.widgets.get("canvas_output")
fqn = f"{catalog}.{schema}"

if not spark.catalog.tableExists(f"{fqn}.{canvas}"):
    print(f"⏳ {fqn}.{canvas} not found yet — build the Designer canvas first (see README), "
          f"set its Output table to '{canvas}', then re-run this notebook.")
    dbutils.notebook.exit("canvas output pending")

# COMMAND ----------

diff = spark.sql(f"""
WITH b AS (SELECT account_code, round(variance,2) variance, status FROM {fqn}.cm_benchmark),
     c AS (SELECT account_code, round(variance,2) variance, status FROM {fqn}.{canvas})
SELECT coalesce(b.account_code, c.account_code) AS account_code,
       b.variance AS b_variance, c.variance AS c_variance,
       b.status AS b_status, c.status AS c_status
FROM b FULL OUTER JOIN c USING (account_code)
WHERE abs(coalesce(b.variance,0) - coalesce(c.variance,0)) > 0.01
   OR b.status IS DISTINCT FROM c.status
""")
n = diff.count()
if n == 0:
    total = spark.table(f"{fqn}.cm_benchmark").count()
    exc = spark.sql(f"SELECT count(*) n FROM {fqn}.cm_benchmark WHERE status='Exception'").collect()[0].n
    print(f"✅ PARITY: all {total} accounts match the coded reconciliation to the penny — "
          f"including the {exc} exceptions.")
else:
    print(f"❌ {n} account(s) differ:")
    display(diff)
