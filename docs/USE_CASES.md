# The use cases (anonymised)

Three finance / audit workflows that run today in a desktop ETL tool (Alteryx / Power Query /
KNIME) plus Python — used here to show the same work on Lakeflow Designer and the wider
Databricks platform. All identifiers, systems and data are generic and synthetic; nothing here
refers to any real organisation. The common thread the team themselves named: the hard part is
the **file interface** — files landing in folders and formatted outputs going back out — not the
logic in the middle.

## UC1 — Cash-flow rec (append two columns to a rolling file)
- **Shape:** every month, across ~20 bank accounts, open each account's bank-rec workbook and
  read a few summary cells off its **Header** sheet (SAP / Accurate / Bank / Control). Compile
  this period's **Current** and **Control** values and **append them as two new columns** onto a
  single **rolling cash-flow file** that carries one column-pair per period across the financial
  year (12 months, then reset). If an account's workbook is missing, a **fallback** reads two
  cells from separate SAP and Bank folders instead of four.
- **The pain today:** the desktop-ETL build needs a five-input positional hack because the tool
  can't hold a variable for the new column's ever-changing position; the "formatted" output is
  produced by copying a template with Format Painter.
- **On the platform:** land the workbooks, lift the header cells, and append two *named* columns
  (the positional problem vanishes); prove parity to a coded benchmark; emit a **formatted
  Excel** automatically. See `demo_01_cashflow_rec/`.

## UC2 — Control sheet (split into category tables, sum them back)
- **Shape:** join a supplier→category lookup onto a payments dataset, split it into **six or
  seven tables** by combinations of category and other fields, then a **summary control sheet**
  that sums the total of each of those tables.
- **Rule:** the parts must **tie back to the whole with 0.00 variance**.
- **On the platform:** a Lakeflow Designer flow (join → derive → aggregate → summary) + parity.
  See `demo_02_control_sheet/`.

## UC3 — Scheduled automation (two Python jobs)
- **3a — file staging:** files land in **two folders** on a schedule; pick, for each report code,
  the **correct version by file name** (not the latest-arrived) and **copy** it to a destination
  folder. No data change — pure file movement.
- **3b — fixed-width BDX:** each day a **fixed-width** file lands; monthly, run through all ~30 of
  last month's files, **parse by position**, tag each row with its source file, run a **contra
  check per file** (the detail rows must sum to that file's contra row), **consolidate** into one
  output, and emit a **run log / summary** of which files tied and which didn't.
- **The question asked:** *does the platform offer scheduled automation and audit logging
  comparable to what we'd build ourselves?*
- **The answer:** yes — via Lakeflow **Jobs** + **Autoloader** + Unity Catalog audit; these are
  Python jobs, not Designer flows. See `demo_03_automation/`.

## What this proves
- **UC1, UC2** — the desktop-ETL join / lookup / aggregate / reconcile work, done visually on a
  governed platform, reconciled to the penny, with formatted output back out.
- **UC3** — the scheduling, autonomous execution and audit trail the desktop tool can't give
  you, from Lakeflow Jobs + Autoloader + Unity Catalog — and files that flow the moment they
  land, so no one moves them by hand.
