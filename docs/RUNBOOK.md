# Designer Recon Accelerator — Runbook (1-hour session)

Presenter guide for the one-hour session: **Lakeflow Designer**, **no code**, **Excel in and out**.
Three use cases. Every table, notebook and file below is a **clickable link**.

> **About this demo.** All data is synthetic. No real organisation, bank, account or payee. A desktop
> ETL tool (Alteryx / Power Query / KNIME) is a *workflow shape*, not a product comparison.

**Say this in the first 20 seconds** (the reassurance that stops the nervous analyst fighting):
*"You still drop your file, exactly like today. A formatted Excel still comes out the other end. And you
can always tie the answer back to your own spreadsheet — nothing is hidden, nothing is taken away from you."*

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
2. **Source ② — add the table `cf_period_extract`** (this month's numbers). *(Reassure the room: this
   isn't a robot changing your figures — it's just this month's workbook cells read in for you, and the
   **`source_file`** column shows the exact workbook each number came from. Show ⑤ here if they look uneasy.)*
3. **Join** — key `account_code`, type **Left** (keep every account).
4. **Prepare → Formula** — add **`Jul_Status`**: type the description *"Reconciled when the Control figure
   is zero, otherwise Exception"* and Designer writes the expression. No SQL box. *(It's the same
   Reconciled/Exception rule you'd write by hand — visible and plain, you can read it back.)*
5. **Select** — rename `current_period` → **`Jul_Current`**, `period_control` → **`Jul_Control`**; untick
   `source` / `source_file`. (The Select operator has a rename field per column — pure clicks.)
6. **Sort** — Exception rows to the top.
7. **Output → `cf_cashflow_rec_designer`** → **Run.**

All seven are **UI operators — no SQL typed, no code written.**

*Faster still — one **✨ Generate** prompt builds the whole flow.* On a blank **+ New → Data prep** canvas, paste:
> *Join the rolling cash-flow file to cf_period_extract on account_code, keeping every account (left join).
> Add a column Jul_Status = "Reconciled" when the control figure is 0 else "Exception". Rename current_period
> to Jul_Current and period_control to Jul_Control, and drop the source and source_file columns. Sort
> Exception rows to the top. Write to cf_cashflow_rec_designer in lr_dev_aws_us_catalog.designer_recon_demo.*

Set Output, **Run**. (This is the recreate-in-Designer prompt — tables as inputs, no Excel drag needed.)

### ④ Prove it + Excel out
- Run **`02_parse_append_parity.py`** → **✅ PARITY to the penny** vs `cf_benchmark`; it writes the
  **formatted Excel** to `output/CashFlowRec_2026-07.xlsx` (+ `.csv`). **5 of 6 reconciled, 1 exception
  (ACC-003)** — shown in red.
- *"Each account's Control nets to zero — that's the reconciliation; the one that doesn't is flagged."*
  *(Frame the red row as a win, not a fault: an exception is exactly what you **want** the tool to surface —
  it's doing your checking for you, not breaking. Nobody broke month-end; the control just did its job.)*

### ⑤ Provenance & audit (show this — it wins the sceptic *and* the auditor)
- **Where every figure came from:** open `cf_period_extract` — the **`source_file`** column shows each
  account's exact workbook (ACC-001 ← `BankRec_ACC-001_2026-07.xlsx`; the missing one ← fallback).
- **What the run did:** `cf_ingest_log` — one row per file, **ok** or **FAILED**. Nothing silently ingested.
- **Who changed the figures, when:** open the table in **Catalog Explorer → History tab** — a UI panel
  listing every version, timestamp, user and operation (no command typed on screen). Flow/logic changes are
  in **git**. That's the auditor-facing answer — an immutable, exportable record, not just a lineage picture.
  *(Presenter aside, if a technical colleague asks: the same thing is `DESCRIBE HISTORY … cf_cashflow_rec`.)*

### ⑥ When they attack — the hard cases (all real, on tap)
- **"What about a bad file?"** Drop a corrupt `.xlsx` into `bank_recs/` and re-run the ingest → it's
  logged **FAILED** in `cf_ingest_log` and **quarantined**; the other accounts still process. (Proven live.)
- **"A missing workbook?"** ACC-006 has none → the **2-cell fallback** covers it (visible in `source_file`).
- **"Does it roll across the year?"** The rolling file already carries **Apr / May / Jun** and you just
  appended **Jul** — one column-pair per period. Next month appends Aug; at month 12 a new FY file starts.
  (Bump the `period` widget to run another month live.)
- **"Six accounts isn't my 200."** *Show it, don't tell it:* bump the generator's `n_accounts` widget to
  50/200 and re-run live (~1 min) — same flow, same parity, more rows. It's **serverless / scale-to-zero**
  (pay for the run, not idle desktops or servers).
- **"This is lock-in — my Alteryx runs on my desktop, I own it."** The opposite: your **Excel/CSV stay in
  your own folders**, the logic is plain **Spark SQL you can view and export** (**</> Code**) and it's
  **git-versioned**, and it runs on **open Delta + Spark** — nothing is trapped in a proprietary binary
  canvas file. You can walk away with your data and your logic any day.

### ⑦ Collaborate & schedule (live, one click each)
- **Co-own it:** **Share → Can Edit** — two people on the *same* governed flow, every change versioned
  (vs emailing `final_v7.xlsx`).
- **Schedule + run history:** the ingest/append run as **Jobs/Pipelines** — set a schedule, show the
  **run history**; runs unattended, no licensed user in the loop.

### ⑧ Only if pushed on the automation — keep it reassuring
*"Your workbooks land in the same folder you use today; the platform reads them so you don't re-key — and
you can see exactly what it used (⑤) and that nothing failed."* That's **Auto Loader** (job
`uc1_ingest_autoloader`): a convenience with full visibility, **not** a black box that took your files away.

*Optional bonus beat, only for a technical questioner who wants to see the file-lands-→-table magic:* the
`demo_00_autoloader` pipeline is a 4-line streaming table that **appends automatically the moment a new Excel
lands** (drop a file, re-run, watch the row count go 3 → 6). Keep it in your back pocket — don't lead with it,
it's the opposite of the "you still drop your file" reassurance the nervous room needs.

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
**For a nervous room, lead with this — click five boxes, none need SQL** (each box is a click or a
plain-English line — this *is* the non-technical route):
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

**The shortcut, for a technical colleague — one ✨ prompt** builds the same flow in one go. *(Offer this as
the fast path, not the beginner path — it packs the whole branch rule into one paragraph.)* On a blank
**+ New → Data prep** canvas, paste:
> *Join Payments to CategoryLookup on supplier, keeping every payment (left join). Add a branch column: if
> there's no category call it "Unmatched (no category)", otherwise company_code + ' ' + (Provider if category
> is Claims, Refund or Travel else NonProvider) + ' ' + (Img2 if account_id is even else Img3). Group by branch
> and sum amount_paid as branch_total. Write to cs_control_sheet_designer in lr_dev_aws_us_catalog.designer_recon_demo.*

Set Output, **Run**. Same result — English in, no SQL. *(The grand total + tie-check is ④, so the canvas stays simple.)*

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
- **See/amend logic:** **</> Code**; **audit:** the table's **History tab** in Catalog Explorer (who/when/what,
  a UI panel — no command on screen) + git. *(Presenter aside: the command form is `DESCRIBE HISTORY … cs_control_sheet`.)*

### ⑥ When they attack — the hard cases (proven, not promised)
- **"Supplier not in the lookup?"** Shown live: **8** such payments land in the **Unmatched** group and stay in
  the total (`cs_population_recon`: 392 + 8 = 400). Not dropped, not hidden.
- **"Duplicate-supplier fan-out / double-count?"** The recon asserts **rows-after-join = rows-in** and **0
  duplicate suppliers** — a fan-out fails the run.
- **"Eight groups isn't my dozens / millions of rows."** *Show it:* bump `n_payments` and re-run live —
  same flow, same 0.00 tie-back at any scale, serverless / scale-to-zero.
- **"Your parity marks its own homework."** Fair — that's the internal check; the **population reconciliation**
  is the correctness check, and we'll **tie it to your exported control total, on your file**, live.
- **"This locks me in."** No — Excel/CSV stay in **your folders**, the logic is exportable **Spark SQL**
  (**</> Code**), **git-versioned**, on **open Delta** — walk away with data *and* logic any time.

### ⑦ Collaborate, schedule & reuse (live)
- **Share → Can Edit** — co-own the same flow, versioned. **Schedule** it as a Job with run history.
- **One definition, everywhere:** point **Genie** or an **AI/BI dashboard** at `cs_control_sheet`. **If a
  technical/keen person is in the room, do it live** — ask *"Provider groups by company, largest first"* in
  plain English and let the answer come back off the same governed numbers. It's a 30-second move that turns
  an interested analyst into an advocate — don't leave it as a "next session" promise if you have the minute.

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

### ① The requirement — what they asked for (say this)
Two Python scripts they run **by hand** today. The question they set: *"can the platform schedule and log
this like our scripts — unattended and audited?"* **Answer: yes — Lakeflow Jobs + Auto Loader + Unity
Catalog audit. No Designer canvas — and that honesty is the point.**
- **3a — file staging:** files land in **two folders**; pick, per report code, the **correct version by
  file name** (not latest-arrived), and **copy** to a destination. No data change.
- **3b — fixed-width BDX:** monthly, run **all ~30** of last month's **fixed-width** files → **parse by
  position** → **contra-check each** (detail rows sum to the file's contra row) → **consolidate** → log.

**The bar:** scheduled · unattended · **audited** · **every file accounted for** (nothing silently dropped,
mis-picked or mis-parsed) · runs like their script, but governed.

### ② The story you tell (governance over cron)
*"You already schedule a script. The difference: it fires the moment a file lands, it can't silently lose
or mis-read a file — every file gets a visible verdict — and the whole run is audited on the platform,
not on someone's laptop."*
*(Reassure the nervous analyst: you still just drop the files, it runs itself on a schedule, and it hands
you a plain summary — **you never open the Python**. This is the part IT sets up once; you just receive it.)*

### ③ Run it (~5 min, no build) + the reconciliation that wins the room
Run jobs **`automation_file_staging`** (3a) and **`automation_bdx_parser`** (3b) — or the notebooks.
- **3a — every file accounted for:** `af_version_audit` marks each file **chosen / superseded /
  unrecognized** and reconciles: **9 seen = 5 chosen + 4 superseded + 0 unrecognized**, 5 copied. You *see*
  which version was picked and why the others weren't — nothing silently ignored.
- **3b — every file statused (value-level, not just count):** `fw_contra_log` gives each file **MATCH /
  MISMATCH / NO CONTRA / PARSE ISSUE / MULTI CONTRA / EMPTY**, asserted to cover **every** landed file —
  here **30 = 27 MATCH + 2 MISMATCH + 1 NO CONTRA**. A ragged line that won't parse → **PARSE ISSUE**
  (never summed as 0); a second contra row → **MULTI CONTRA** (never double-counted).
- **The point:** Job **run history** + these audit tables + Catalog **lineage** = scheduled, unattended,
  **audited** — and it **fails loudly**, it never hides a bad file behind a green tick.

### ④ Trust & audit
- The status logs *are* the audit: who ran it (run history), which file was used/rejected and why
  (`af_version_audit`), which files didn't tie (`fw_contra_log`). Plus each table's **History tab** in
  Catalog Explorer + git on the code.
- The **asserts are DQ gates** — the file-count and value-level checks **fail the run** if anything is
  unaccounted for, so the control can't silently pass.

### ⑤ When they attack — honest answers
- **"A bad file — no contra / empty / a shifted column?"** Shown: NO CONTRA / EMPTY / **PARSE ISSUE** —
  flagged and kept out of the totals, not silently absorbed. (Proven live.)
- **"Nobody's paged when it breaks — my macro at least errors on my screen."** The opposite: **Job failure
  notifications are native and out of the box** — email / Slack / PagerDuty / webhook on failure (or on a DQ
  gate tripping), set with a click. You're *more* likely to know it broke than with a script on one laptop.
- **"cron already does this."** True for the middle; the platform adds **on-arrival triggering, governed
  audit + lineage, DQ gates, failure alerting, and no desktop dependency** — the same governed home as UC1/UC2.
- **Known edges — we'll be straight (roadmap, not claimed):** "highest version by name" is a heuristic (a
  *re-issued* older version needs a smarter `supersedes`/effective-date rule); **idempotent single-file
  re-run**; and **big-volume patterns** (the demo notebooks list/collect at small scale). We name these
  rather than pretend — each is a standard platform pattern to add.

### Assets — kept small (2 folders / 5 codes; ~30 daily files)
Volume `recon_landing/`: **3a** `uc3a/sources/{folder_a,folder_b}` → `uc3a/destination`; **3b**
`uc3b/incoming` → `uc3b/output` (consolidated CSV + `run_summary_*.txt`).
Tables (`explore/data/lr_dev_aws_us_catalog/designer_recon_demo/…`): `af_version_audit` · `af_files_staged` ·
`af_staging_audit` (3a) · `fw_bdx_consolidated` · `fw_contra_log` (3b).
Notebooks (GitHub; run in workspace `/Workspace/Shared/designer-recon-accelerator/demo_03_automation/…`):
3a — https://github.com/wryszka/designer-recon-accelerator/blob/main/demo_03_automation/01_file_staging.py ·
3b — https://github.com/wryszka/designer-recon-accelerator/blob/main/demo_03_automation/02_fixedwidth_parser.py

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
