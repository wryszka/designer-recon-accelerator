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
- **Notebooks (code):** https://github.com/wryszka/designer-recon-accelerator — *to open/run, in the workspace go to `Workspace → Shared → designer-recon-accelerator`*
- **All tables:** https://fevm-lr-dev-aws-us.cloud.databricks.com/explore/data/lr_dev_aws_us_catalog/designer_recon_demo
- **Files (Volume `recon_landing`):** https://fevm-lr-dev-aws-us.cloud.databricks.com/explore/data/volumes/lr_dev_aws_us_catalog/designer_recon_demo/recon_landing

Each use case below: **① the requirement** (say this to walk them through it) · **② assets** (links) ·
**③ build it — no code** · **④ prove it**. **UC1 & UC2 are Designer flows. UC3 is NOT — it's scheduled
Jobs (that's the point of UC3).**

---

# UC1 — Cash-flow reconciliation  *(the hero, ~half the session)*

### ① The requirement — what they asked for (say this to walk them through it)
A **monthly** job across their bank accounts. Each account has a **bank-rec workbook** in a folder;
someone reads a few summary cells off its header (**SAP / Accurate / Bank / Control**) and **appends two
new columns** — this period's **Current** and **Control** — onto last month's **rolling** file (one
column-pair per month; 12 months, then a new financial year). If a workbook is **missing**, they fall
back to two cells from a separate SAP/Bank folder. Output must be a **formatted Excel**. Today it's an
ugly five-input Alteryx build (the tool can't hold a variable for the moving column position) and the
"format" is a manual Format-Painter copy.

**The bar they'll judge on:** no code / accessible · trustable (see & change the logic) · a colleague can
co-own it · scheduled + audited · handles the missing workbook · **each account nets to zero** with
exceptions flagged · formatted Excel out.

### ② The story you tell while building
*"You drop your rolling cash-flow file — the one you carry forward. This month's account numbers are
already here as a table, and you can see exactly which workbook each figure came from. We join them,
reconcile, and hand you back a formatted Excel. No code, nothing re-keyed."* Keep it familiar — **you
drop a file**, like today — and lean on **provenance** (⑤) so nothing feels like a black box.

### ③ Build the flow — no code, all visual UI operators (7 boxes)
Designer's operators do every step with **no SQL**: rename via the **Select** operator, derive via
**Prepare → Formula** (you type a plain-English *description* in the Formula box — it is **not** a SQL box).
1. **Source ① — drop the Excel:** drag **`rolling/CashFlowRec_2026-06.xlsx`** onto the canvas (the ONE
   file). *(csv sits beside it if you'd rather drop csv.)*
2. **Source ② — add the table `cf_period_extract`** (this month's numbers).
3. **Join** — key `account_code`, type **Left** (keep every account).
4. **Prepare → Formula** — add **`Jul_Status`**: type the description *"Reconciled when period_control is
   0, otherwise Exception"* and Designer writes the expression. No SQL box.
5. **Select** — rename `current_period` → **`Jul_Current`**, `period_control` → **`Jul_Control`**; untick
   `source` / `source_file`. (The Select operator has a rename field per column — pure clicks.)
6. **Sort** — Exception rows to the top.
7. **Output → `cf_cashflow_rec_designer`** → **Run.**

All seven are **UI operators — no SQL typed, no code written.** *(Faster still: one **✨ Generate** prompt
builds the whole flow — the recreate prompt is in the Fallbacks section.)*

### ④ Prove it + Excel out
- Run **`02_parse_append_parity.py`** → **✅ PARITY to the penny** vs `cf_benchmark`; it writes the
  **formatted Excel** to `output/CashFlowRec_2026-07.xlsx` (+ `.csv`). **5 of 6 reconciled, 1 exception
  (ACC-003)** — shown in red.
- *"Each account's Control nets to zero — that's the reconciliation; the one that doesn't is flagged."*

### ⑤ Provenance & audit (show this — it wins the sceptic *and* the auditor)
- **Where every figure came from:** open `cf_period_extract` — the **`source_file`** column shows each
  account's exact workbook (ACC-001 ← `BankRec_ACC-001_2026-07.xlsx`; the missing one ← fallback).
- **What the run did:** `cf_ingest_log` — one row per file, **ok** or **FAILED**. Nothing silently ingested.
- **Who changed the figures, when:** `DESCRIBE HISTORY lr_dev_aws_us_catalog.designer_recon_demo.cf_cashflow_rec`
  (version, timestamp, user, operation); flow/logic changes are in **git**. That's the auditor answer —
  not just a lineage picture.

### ⑥ When they attack — the hard cases (all real, on tap)
- **"What about a bad file?"** Drop a corrupt `.xlsx` into `bank_recs/` and re-run the ingest → it's
  logged **FAILED** in `cf_ingest_log` and **quarantined**; the other accounts still process. (Proven live.)
- **"A missing workbook?"** ACC-006 has none → the **2-cell fallback** covers it (visible in `source_file`).
- **"Does it roll across the year?"** The rolling file already carries **Apr / May / Jun** and you just
  appended **Jul** — one column-pair per period. Next month appends Aug; at month 12 a new FY file starts.
  (Bump the `period` widget to run another month live.)
- **"Six accounts isn't my 200."** Same flow, any volume — the generator's `n_accounts` scales it, and
  it's **serverless / scale-to-zero** (pay for the run, not idle desktops or servers).

### ⑦ Collaborate & schedule (live, one click each)
- **Co-own it:** **Share → Can Edit** — two people on the *same* governed flow, every change versioned
  (vs emailing `final_v7.xlsx`).
- **Schedule + run history:** the ingest/append run as **Jobs/Pipelines** — set a schedule, show the
  **run history**; runs unattended, no licensed user in the loop.

### ⑧ Only if pushed on the automation — keep it reassuring
*"Your workbooks land in the same folder you use today; the platform reads them so you don't re-key — and
you can see exactly what it used (⑤) and that nothing failed."* That's **Auto Loader** (job
`uc1_ingest_autoloader`): a convenience with full visibility, **not** a black box that took your files away.

### Assets — kept deliberately small (6 accounts; scale up if they ask)
Volume `recon_landing/uc1/` — a few examples, **xlsx and csv**:
- **drag this →** `rolling/CashFlowRec_2026-06.xlsx` (also `.csv`)
- account workbooks (5) → `bank_recs/` · the missing-account fallback → `fallback/`
- **formatted output →** `output/CashFlowRec_2026-07.xlsx` (also `.csv`)

Tables (`explore/data/lr_dev_aws_us_catalog/designer_recon_demo/…`): `cf_prior_rec` (rolling) ·
`cf_period_extract` (this month, with `source_file` provenance) · `cf_cashflow_rec` (result) ·
`cf_benchmark` (oracle) · `cf_ingest_log` (audit: ok/FAILED per file).

Notebooks (code on GitHub; run them in the workspace at `/Workspace/Shared/designer-recon-accelerator/demo_01_cashflow_rec/…`):
- generate: https://github.com/wryszka/designer-recon-accelerator/blob/main/demo_01_cashflow_rec/01_generate_sources.py
- Autoloader ingest (job `uc1_ingest_autoloader`): https://github.com/wryszka/designer-recon-accelerator/blob/main/demo_01_cashflow_rec/00_ingest_autoloader.py
- parity + Excel (job `uc1_parse_append_parity`): https://github.com/wryszka/designer-recon-accelerator/blob/main/demo_01_cashflow_rec/02_parse_append_parity.py

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
- code: https://github.com/wryszka/designer-recon-accelerator/blob/main/demo_02_control_sheet/02_parity.py · open in workspace at `/Workspace/Shared/designer-recon-accelerator/demo_02_control_sheet/02_parity`
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
- **3a** — run as job **`automation_file_staging`**; code: https://github.com/wryszka/designer-recon-accelerator/blob/main/demo_03_automation/01_file_staging.py · tables `af_files_staged`, `af_staging_audit` (https://fevm-lr-dev-aws-us.cloud.databricks.com/explore/data/lr_dev_aws_us_catalog/designer_recon_demo/af_staging_audit)
- **3b** — run as job **`automation_bdx_parser`**; code: https://github.com/wryszka/designer-recon-accelerator/blob/main/demo_03_automation/02_fixedwidth_parser.py · tables `fw_bdx_consolidated`, `fw_contra_log` (https://fevm-lr-dev-aws-us.cloud.databricks.com/explore/data/lr_dev_aws_us_catalog/designer_recon_demo/fw_contra_log)

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
