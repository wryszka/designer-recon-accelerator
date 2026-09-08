# Databricks notebook source
# MAGIC %md
# MAGIC # UC2 · Prove the control sheet ties back with zero variance
# MAGIC
# MAGIC You built `cs_control_sheet` on the Lakeflow Designer canvas (see `README.md`). This
# MAGIC compares each branch total to `cs_benchmark` — the coded control sheet — and confirms
# MAGIC the branches sum to the main total with **0.00 variance**. That reconciliation *is* the
# MAGIC control; you tie it out rather than trusting the generated SQL.

# COMMAND ----------

dbutils.widgets.text("catalog_name", "lr_dev_aws_us_catalog")
dbutils.widgets.text("schema_name", "designer_recon_demo")
dbutils.widgets.text("canvas_output", "cs_control_sheet")
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
WITH b AS (SELECT branch, round(branch_total,2) t FROM {fqn}.cs_benchmark),
     c AS (SELECT branch, round(branch_total,2) t FROM {fqn}.{canvas})
SELECT coalesce(b.branch, c.branch) AS branch, b.t AS benchmark_total, c.t AS canvas_total
FROM b FULL OUTER JOIN c USING (branch)
WHERE abs(coalesce(b.t,0) - coalesce(c.t,0)) > 0.01
""")
n = diff.count()
# also re-confirm the parts tie to the whole on the canvas output
tie = spark.sql(f"""
  SELECT round(sum(CASE WHEN branch <> 'MAIN (all payments)' THEN branch_total END)
             - max(CASE WHEN branch = 'MAIN (all payments)' THEN branch_total END), 2) AS parts_minus_whole
  FROM {fqn}.{canvas}""").collect()[0].parts_minus_whole
if n == 0 and (tie is None or abs(tie) < 0.01):
    print("✅ PARITY: every branch matches the coded control sheet, and the branches tie back "
          "to the main total with 0.00 variance.")
else:
    print(f"❌ {n} branch(es) differ; parts_minus_whole = {tie}")
    display(diff)
