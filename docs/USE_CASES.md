# The use cases (anonymised)

Three finance / audit reconciliation workflows that run today in a desktop ETL tool
(Alteryx / Power Query / KNIME) plus Python — used here to show the same work on Lakeflow
Designer and the wider Databricks platform. All identifiers, systems and data are generic and
synthetic; nothing here refers to any real organisation.

## UC1 — Cash matching (bank reconciliation)
- **Shape:** reconcile ~40+ bank accounts at period end, pulling balances from a ledger/ERP
  export, a bank-statement feed and the prior-period baseline.
- **Rule:** for each account, ledger closing = bank closing once timing (outstanding) items
  are accounted for — i.e. it **nets to zero**. Accounts with a residual variance are
  **exceptions** an auditor must see.
- **Output:** a per-account reconciliation with a variance and a Reconciled / Exception status
  (an auditable trail).
- **On the platform:** a Lakeflow Designer flow (join → SQL → output) + parity to a coded
  benchmark. See `demo_01_cash_matching/`.

## UC2 — Control sheet (branch reconciliation)
- **Shape:** join a supplier→category lookup onto a payments dataset, split into several
  branches (by company, category and bank), total each on a control sheet.
- **Rule:** every branch must **tie back to the main dataset with 0.00 variance**.
- **On the platform:** a Lakeflow Designer flow (join → derive branch → aggregate → union →
  output) + parity. See `demo_02_control_sheet/`.

## UC3 — Scheduled automation (Python)
- **Shape:** two Python jobs — (a) scan folders and stage the earliest version of each report
  for a period; (b) parse a fixed-width payment export by column position, net contra
  reversals, consolidate and validate.
- **The question asked:** *does the platform offer scheduled automation and audit logging
  comparable to what we'd build ourselves?*
- **The answer:** yes — via Lakeflow **Jobs** + **Autoloader** + Unity Catalog audit; these
  are Python jobs, not Designer flows. See `demo_03_automation/`.

## What this proves
- **UC1, UC2** — the desktop-ETL join/clean/aggregate/reconcile work, done visually on a
  governed platform, reconciled to the penny.
- **UC3** — the scheduling, autonomous execution and audit trail the desktop tool can't give
  you, from Lakeflow Jobs + Autoloader + Unity Catalog.
