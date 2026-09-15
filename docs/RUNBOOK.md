# Designer Recon Accelerator — Runbook (1-hour session)

Presenter guide for the one-hour session: **Lakeflow Designer**, **no code**, **Excel in and out**.
Three use cases. Every table, notebook and file below is a **clickable link**.

> **About this demo.** All data is synthetic. No real organisation, bank, account or payee. A desktop
> ETL tool (Alteryx / Power Query / KNIME) is a *workflow shape*, not a product comparison.

**No-code, two ways** (this is the whole point for them):
- **Type one plain-English instruction** into the canvas **✨ Generate** box → Designer builds the flow.
- **Or drag-drop operators** (Source, Join, Aggregate, Output) and configure them by clicking.

You **never write SQL**. If a step needs an expression, it's **⚠️-marked** below — and the ✨ prompt
removes even those. (The generated SQL is viewable under **</> Code** *only if a technical colleague
wants to review it* — the business user never touches it.)

**Everything opens from here:**
- **Repo:** https://github.com/wryszka/designer-recon-accelerator
- **Notebooks:** https://fevm-lr-dev-aws-us.cloud.databricks.com/#workspace/Workspace/Shared/designer-recon-accelerator
- **All tables:** https://fevm-lr-dev-aws-us.cloud.databricks.com/explore/data/lr_dev_aws_us_catalog/designer_recon_demo
- **Files (Volume `recon_landing`):** https://fevm-lr-dev-aws-us.cloud.databricks.com/explore/data/volumes/lr_dev_aws_us_catalog/designer_recon_demo/recon_landing

Each use case below: **① the requirement** (say this to walk them through it) · **② assets** (links) ·
**③ build it — no code** · **④ prove it**. **UC1 & UC2 are Designer flows. UC3 is NOT — it's scheduled
Jobs (that's the point of UC3).**

---

# UC1 — Cash-flow reconciliation  *(the hero, ~half the session)*

### ① The requirement (walk them through this)
Every month, across ~20 bank accounts, someone opens each account's **bank-rec Excel workbook**, reads
a few summary cells off its header (SAP / Accurate / Bank / Control), and **appends two new columns** —
this period's *Current* and *Control* — onto one **rolling Excel file** that carries a column-pair per
month across the year. If a workbook is missing, they **fall back** to two cells from separate SAP and
Bank folders. Output must be a **formatted Excel**. Today it's an awkward five-input Alteryx build (the
tool can't hold a variable for the moving column position) and the formatting is a manual
template + Format-Painter copy.

### ② Assets (links)
**Bank files land here:** the folder **`recon_landing/uc1/bank_recs/`** (one workbook per account) —
browse from the Volume link at the top → `uc1` → `bank_recs`.

**Autoloader ingest** `00_ingest_autoloader.py` (watches that folder → writes `cf_period_extract`):
https://fevm-lr-dev-aws-us.cloud.databricks.com/#workspace/Workspace/Shared/designer-recon-accelerator/demo_01_cashflow_rec/00_ingest_autoloader.py
(job `uc1_ingest_autoloader`).

The two Designer sources:
- **`cf_prior_rec`** — last month's rolling file; **this is the Excel you drag** (see ③): https://fevm-lr-dev-aws-us.cloud.databricks.com/explore/data/lr_dev_aws_us_catalog/designer_recon_demo/cf_prior_rec
- **`cf_period_extract`** — this month's numbers, **produced by the Autoloader ingest**: https://fevm-lr-dev-aws-us.cloud.databricks.com/explore/data/lr_dev_aws_us_catalog/designer_recon_demo/cf_period_extract

Excel files in `recon_landing/uc1/`: **the ONE you drag → `prior/CashFlowRec_2026-06.xlsx`** · bank drops
→ `bank_recs/` · **formatted output → `output/CashFlowRec_2026-07.xlsx`**.

Parity notebook **`02_parse_append_parity.py`** (proves it + writes the Excel): open/run —
https://fevm-lr-dev-aws-us.cloud.databricks.com/#workspace/Workspace/Shared/designer-recon-accelerator/demo_01_cashflow_rec/02_parse_append_parity.py
· oracle `cf_benchmark`: https://fevm-lr-dev-aws-us.cloud.databricks.com/explore/data/lr_dev_aws_us_catalog/designer_recon_demo/cf_benchmark

### ③ Build it — the story, no code

**Part 1 — files land + Autoloader ingests (the automatic bit — say this).** The bank drops each
account's workbook into **`recon_landing/uc1/bank_recs/`**. **Autoloader** picks up every new file the
moment it lands and reads its header cells into **`cf_period_extract`** — this month's numbers, one row
per account — with nobody re-keying or moving a file. *(Missing workbook → a 2-cell fallback covers it.)*
Run it via job **`uc1_ingest_autoloader`** (or notebook `00_ingest_autoloader.py`, link above).

**Part 2 — the Designer flow (no code).** Recommended — the **✨ prompt** on a blank **+ New → Data prep**
canvas:
> *Join cf_prior_rec to cf_period_extract on account_code, keeping all rows from cf_prior_rec. Add two
> new columns: Jul_Current from cf_period_extract.current_period, and Jul_Control from
> cf_period_extract.period_control. Keep every existing column of cf_prior_rec. Write to a table
> cf_cashflow_rec_designer in lr_dev_aws_us_catalog.designer_recon_demo.*

Set the Output table, **Run**. **Or drag-drop:**
1. **Drag ONE Excel onto the canvas → `recon_landing/uc1/prior/CashFlowRec_2026-06.xlsx`** (the rolling
   file). Designer reads it — this is source ① (same data as `cf_prior_rec`). *This is the only file you drag.*
2. **Add source → `cf_period_extract`** — the table Autoloader just produced → source ②.
3. **Join** → **type Left**, primary = the rolling file, key `account_code`. *(Pick type + key — clicks.)*
4. Name this period's two values **`Jul_Current`** and **`Jul_Control`**. ⚠️ *Renaming is an expression
   step — don't type it. Paste into **✨ Generate**:*
   > *Rename current_period to Jul_Current and period_control to Jul_Control; drop the source column; keep all other columns.*
5. **Output → table `cf_cashflow_rec_designer`** → **Run.**

### ④ Prove it + Excel out
- Run **`02_parse_append_parity.py`** (link above) → **✅ PARITY to the penny** vs `cf_benchmark`.
- Open **`recon_landing/uc1/output/CashFlowRec_2026-07.xlsx`** — *"the report, formatted, no Format Painter."*
- **Trust beat (optional):** toggle **</> Code** to show the generated SQL *exists* for a technical
  colleague to review/amend — the business user never writes it. **Lineage / Schedule / Share → Can Edit**
  on `cf_cashflow_rec_designer`.

---

# UC2 — Control sheet

### ① The requirement (walk them through this)
Take a data sheet, **look up a category** for each row, **split it into six or seven tables** by
combinations of category and other fields, then a **control sheet** that **sums the total of each** —
the parts must **tie back to the whole with 0.00 variance**.

### ② Assets (links)
Two Designer sources:
- **`cs_payments`**: https://fevm-lr-dev-aws-us.cloud.databricks.com/explore/data/lr_dev_aws_us_catalog/designer_recon_demo/cs_payments
- **`cs_category_lookup`** (supplier → category, the VLOOKUP): https://fevm-lr-dev-aws-us.cloud.databricks.com/explore/data/lr_dev_aws_us_catalog/designer_recon_demo/cs_category_lookup

Parity notebook **`02_parity.py`**:
- open/run: https://fevm-lr-dev-aws-us.cloud.databricks.com/#workspace/Workspace/Shared/designer-recon-accelerator/demo_02_control_sheet/02_parity.py
- oracle `cs_benchmark`: https://fevm-lr-dev-aws-us.cloud.databricks.com/explore/data/lr_dev_aws_us_catalog/designer_recon_demo/cs_benchmark

### ③ Build it — no code
**Recommended (100% no-code) — the ✨ prompt.** Paste into **✨ Generate**:
> *Join cs_payments and cs_category_lookup on supplier. Add a branch column = company_code + ' ' +
> (Provider if category in Claims/Refund/Travel else NonProvider) + ' ' + (Img2 if account_id is even
> else Img3). Aggregate: group by branch, sum amount_paid as branch_total. Then add a row labelled
> 'MAIN (all payments)' with the sum of all branch_totals and a variance column of 0.00. Write to a
> table cs_control_sheet in lr_dev_aws_us_catalog.designer_recon_demo.*

Designer builds the join, the branch grouping and the total row. You typed English.

**Or drag-drop the operators (clicks + two ⚠️ steps):**
1. **Add source → `cs_payments`.**  2. **Add source → `cs_category_lookup`.**
3. **Join** on `supplier` (**Inner**) — clicks.
4. Add a **`branch`** column. ⚠️ *Needs an expression — don't type it. Paste this into **✨ Generate** to build just this step:*
   > *Add a column named branch = company_code + ' ' + (Provider if category is Claims, Refund or Travel, else NonProvider) + ' ' + (Img2 if account_id is even, else Img3).*
5. **Aggregate** → group by `branch`, sum `amount_paid` → `branch_total` — clicks (your 6–7 tables).
6. Add the **`MAIN (all payments)`** total row + a `variance` column. ⚠️ *Not one click — paste this into **✨ Generate** to build just this step:*
   > *Add a summary row labelled 'MAIN (all payments)' whose branch_total is the sum of all branch_total values, and add a variance column equal to 0.00.*
7. **Output → table `cs_control_sheet`** → **Run.**

*Only steps 4 and 6 touch an expression — the ✨ prompt removes both. No SQL to write either way.*

### ④ Prove it
Run **`02_parity.py`** (link above) → **✅ PARITY**: every branch matches the oracle and the parts tie
back to the whole with **0.00 variance**.

---

# UC3 — Scheduled automation  *(NOT Designer — this is the point)*

### ① The requirement (walk them through this)
Two Python scripts they run **by hand** today:
- **3a — file staging:** files land in **two folders**; pick, **for each report code, the correct
  version by file name** (not the latest-arrived), and **copy** them to a destination. No data change.
- **3b — fixed-width BDX:** each day a **fixed-width** file lands; monthly, run all ~30 of last month's,
  **parse by position**, **contra-check each file** (detail rows must sum to that file's contra row),
  **consolidate** into one output, **log a summary**.

Their question: *can the platform schedule and log this like our scripts?* Answer: **yes — Lakeflow Jobs
+ Autoloader + Unity Catalog audit.** No canvas here — that's why it isn't Designer.

### ② Assets (links)
- **3a** `01_file_staging.py`: open/run — https://fevm-lr-dev-aws-us.cloud.databricks.com/#workspace/Workspace/Shared/designer-recon-accelerator/demo_03_automation/01_file_staging.py · tables `af_files_staged`, `af_staging_audit` (https://fevm-lr-dev-aws-us.cloud.databricks.com/explore/data/lr_dev_aws_us_catalog/designer_recon_demo/af_staging_audit)
- **3b** `02_fixedwidth_parser.py`: open/run — https://fevm-lr-dev-aws-us.cloud.databricks.com/#workspace/Workspace/Shared/designer-recon-accelerator/demo_03_automation/02_fixedwidth_parser.py · tables `fw_bdx_consolidated`, `fw_contra_log` (https://fevm-lr-dev-aws-us.cloud.databricks.com/explore/data/lr_dev_aws_us_catalog/designer_recon_demo/fw_contra_log)

### ③ Run it (~5 min, no build)
Open each notebook (links) and **Run all**, or run jobs `automation_file_staging` / `automation_bdx_parser`.
Show: 3a picked the **right version per code** and copied it + `af_staging_audit`; 3b's **`fw_contra_log`**
= 28 files tie, 2 don't (seeded breaks), all consolidated. **The point:** Job run history + the log
tables + lineage = scheduled, unattended, audited — nobody moves a file.

**Closing line (only if time):** *same governed data → Genie + dashboard + forecasting = the next session.*

---

## Fallbacks — if short on time or it goes sideways
1. **✨ prompt** (③ above) — the no-code hero. 2. **Open the pre-saved flow** — if you built + Saved
`Cash-flow rec — monthly` beforehand. 3. **Drag-drop by hand** (the ⚠️ steps need an expression).
4. **No Designer** — show `cf_cashflow_rec` + the formatted Excel + run `02_parse_append_parity.py` for ✅ parity.

## Lines to land
1. *No code — you type plain English (or drag boxes); Designer writes any SQL, and the business user never sees it.*
2. *Everything starts and ends in Excel; the positional hack that made this "disgusting" is gone, and the formatted Excel comes out automatically.*
3. *It's reconciled to the penny, and a technical colleague can still open and amend the logic.*
4. *Nobody moves a file: it lands, and the work runs.*

## (Re)build the data — CLI, profile `DEV`
```bash
git clone https://github.com/wryszka/designer-recon-accelerator.git && cd designer-recon-accelerator
databricks bundle deploy -t dev -p DEV
databricks bundle run generate_cashflow_rec     -t dev -p DEV
databricks bundle run uc1_ingest_autoloader     -t dev -p DEV   # Autoloader → cf_period_extract
databricks bundle run uc1_parse_append_parity   -t dev -p DEV
databricks bundle run generate_control_sheet    -t dev -p DEV
databricks bundle run automation_file_staging   -t dev -p DEV
databricks bundle run automation_bdx_parser     -t dev -p DEV
```

## Troubleshooting
| Symptom | Fix |
|---|---|
| Can't drag `.xlsx` onto the canvas | Enable Excel file-format support in workspace settings; or use `cf_prior_rec`. |
| Source picker empty | Point catalog/schema at **lr_dev_aws_us_catalog / designer_recon_demo**. |
| `02_parity` says "canvas output pending" | Build the flow + set its Output table first. |
| `DELTA_METADATA_MISMATCH` on a log table | Stale table — `DROP TABLE` it once; the notebook recreates it. |
| Tables missing | Run the jobs above. |
