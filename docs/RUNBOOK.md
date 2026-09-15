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

### ① The requirement — what they asked for (say this)
Two datasets: a **payments** sheet and a **supplier → category** lookup. **Look up** the category onto
each payment, **split into the six-or-seven groups** they report by (category + company + image group),
and a **control sheet** that **sums each group** — and the parts must **tie back to the whole with 0.00
variance**. That tie-back *is* the control.

**The bar:** no code / accessible · trustable + parity · co-own · scheduled + audited · Excel in / out ·
the parts tie to the whole.

### ② The story you tell
*"You drop your payments sheet and your category list; we look up each payment's category, group them the
way you report, and prove **every single payment** is accounted for and the groups add back to the total — to
the penny. Even a payment whose supplier isn't in the category list shows up as its own **Unmatched** group,
so the total is always the true whole. No code, nothing re-keyed."*

### ③ Build the flow — no code, all UI operators (very easy — here's exactly how)
**Easiest — one ✨ prompt** (best for a non-technical build). On a blank **+ New → Data prep** canvas, paste:
> *Join Payments to CategoryLookup on supplier, keeping every payment (left join). Add a branch column: if
> there's no category call it "Unmatched (no category)", otherwise company_code + ' ' + (Provider if category
> is Claims, Refund or Travel else NonProvider) + ' ' + (Img2 if account_id is even else Img3). Group by branch
> and sum amount_paid as branch_total. Write to cs_control_sheet_designer in lr_dev_aws_us_catalog.designer_recon_demo.*

Set Output, **Run**. Done — you typed English, no SQL. *(The grand total + tie-check is ④, so the canvas stays simple.)*

**Or click the operators — five boxes, none need SQL:**
1. **Source ① — drop `inputs/Payments.xlsx`.**  2. **Source ② — drop `inputs/CategoryLookup.xlsx`.** *(both files; csv beside each.)*
3. **Join** — *how: drop a **Join**, wire both in, pick `supplier` on each side, choose **Left join** — "keep
   every payment; never drop one just because its category is missing."*
4. **Add the `branch` group** — *how (easy): drop a **Prepare** operator → **Formula** → type in plain English:
   "if category is empty, 'Unmatched (no category)', else company_code then Provider if category is
   Claims/Refund/Travel else NonProvider then Img2 if account_id is even else Img3." Designer writes it — no SQL.*
5. **Total each group** — *how: drop an **Aggregate** → group by `branch` → sum `amount_paid` → `branch_total`.*
6. **Output → `cs_control_sheet_designer`** → **Run.**

Five boxes, each a click or a plain-English line — **no SQL.** The grand total and the tie-back are the
**check** in ④, so you never hand-build a total row that could drift.

### ④ Prove it — population reconciliation + Excel out (the beat that wins the room)
Run **`02_parity.py`** (job `uc2_control_sheet_parity`). It doesn't just flash "0.00" — it proves the total is
the **whole population**:
- **Every payment accounted for:** `400 in = 392 matched + 8 unmatched` — **0 dropped**.
- **No double-counting:** rows after the join = 400; **0 duplicate suppliers** in the lookup — **0 fan-out**.
- **Groups sum to all payments:** Σ groups = Σ all = **−322,322.44**, **variance 0.00** — including the Unmatched group.
- Writes the **formatted control sheet** to `output/ControlSheet.xlsx` (+ `.csv`): **Unmatched in red, MAIN in bold**.

*"The one thing a control exists to catch — a missing or duplicated supplier quietly wrecking the total — is
exactly what this reconciles. Nothing hides behind a green 0.00."* (See table `cs_population_recon`.)

### ⑤ Trust & audit
- **Lineage drill-through (Excel can't):** in Catalog Explorer, trace a group total → the aggregate → the join
  → the actual payment rows. Click a number, see the payments behind it.
- **The check is a gate, not decoration:** the population/parity assert **fails the run** if the control ever
  breaks — it can't silently go wrong.
- **See/amend logic:** **</> Code**; **audit:** `DESCRIBE HISTORY … cs_control_sheet` (who/when/what) + git.

### ⑥ When they attack — the hard cases (proven, not promised)
- **"Supplier not in the lookup?"** Shown live: **8** such payments land in the **Unmatched** group and stay in
  the total (`cs_population_recon`: 392 + 8 = 400). Not dropped, not hidden.
- **"Duplicate-supplier fan-out / double-count?"** The recon asserts **rows-after-join = rows-in** and **0
  duplicate suppliers** — a fan-out fails the run.
- **"Eight groups isn't my dozens / millions of rows."** Same flow at any scale — `n_payments` bumps it,
  serverless / scale-to-zero.
- **"Your parity marks its own homework."** Fair — that's the internal check; the **population reconciliation**
  is the correctness check, and we'll **tie it to your exported control total, on your file**, live.

### ⑦ Collaborate, schedule & reuse (live)
- **Share → Can Edit** — co-own the same flow, versioned. **Schedule** it as a Job with run history.
- **One definition, everywhere:** point **Genie** or an **AI/BI dashboard** at `cs_control_sheet` — ask "Provider
  groups over time" in plain English, off the same governed numbers (the wider-platform / next-session tail).

### Assets — small & legible (~400 payments → 8 groups + Unmatched)
Volume `recon_landing/uc2/` — **xlsx + csv**: **drag** `inputs/Payments.xlsx` **and** `inputs/CategoryLookup.xlsx`;
**output** `output/ControlSheet.xlsx` (+ `.csv`).
Tables (`explore/data/lr_dev_aws_us_catalog/designer_recon_demo/…`): `cs_payments` · `cs_category_lookup` ·
`cs_control_sheet` (result) · `cs_benchmark` (oracle) · `cs_population_recon` (rows in = grouped, 0 dropped/dup).
Notebooks (GitHub; run in workspace `/Workspace/Shared/designer-recon-accelerator/demo_02_control_sheet/…`):
generate — https://github.com/wryszka/designer-recon-accelerator/blob/main/demo_02_control_sheet/01_generate_sources.py ·
parity + recon + Excel (job `uc2_control_sheet_parity`) — https://github.com/wryszka/designer-recon-accelerator/blob/main/demo_02_control_sheet/02_parity.py

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
