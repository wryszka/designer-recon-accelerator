# Designer Recon Accelerator — Runbook (1-hour session)

Presenter guide for the one-hour session: **Lakeflow Designer**, **no code**, **Excel in and out**.
**Nothing you open in this session is code** — only a spreadsheet-style grid, an Excel file, or the visual
canvas. Three use cases.

> **About this demo.** All data is synthetic. No real organisation, bank, account or payee. A desktop
> ETL tool (Alteryx / Power Query / KNIME) is a *workflow shape*, not a product comparison.

**Say this in the first 20 seconds** (the reassurance that stops the nervous analyst fighting):
*"You still drop your file, exactly like today. A formatted Excel still comes out the other end. And you
can always tie the answer back to your own spreadsheet — nothing is hidden, nothing is taken away from you."*

**No-code, two ways** (this is the whole point for them):
- **Type one plain-English instruction** into the canvas **✨ Generate** box → Designer builds the flow, **or**
- **drag-drop operators** (Source, Join, Aggregate, Output) and configure them by clicking.

The only thing you ever type is **plain English**. **There is no code, no SQL, and no script anywhere in
this session.** *(The synthetic data was built once before the room by a technical setup you never open —
that lives outside this doc; see the last line.)*

**Everything opens from here — all no-code surfaces:**
- **Tables (open as spreadsheet-style grids):** https://fevm-lr-dev-aws-us.cloud.databricks.com/explore/data/lr_dev_aws_us_catalog/designer_recon_demo
- **Files (Excel in / out, the `recon_landing` folder):** https://fevm-lr-dev-aws-us.cloud.databricks.com/explore/data/volumes/lr_dev_aws_us_catalog/designer_recon_demo/recon_landing

Each use case below: **① the requirement** (say this to walk them through it) · **② the story** ·
**③ build it — no code** · **④ prove it — open a grid or the Excel**. **UC1 & UC2 are Designer flows;
UC3 is scheduled runs you start with a button (that's the point of UC3).**

---

# UC1 — Cash-flow reconciliation  *(the hero, ~half the session)*

### ① The requirement — what they asked for (say this)
A **monthly** job across their bank accounts. Each account has a **bank-rec workbook** in a folder;
someone reads a few summary cells off its header (**SAP / Accurate / Bank / Control**) and **appends two
new columns** — this period's **Current** and **Control** — onto last month's **rolling** file (one
column-pair per month; 12 months, then a new financial year). If a workbook is **missing**, they fall
back to two cells from a separate SAP/Bank folder. Output must be a **formatted Excel**. Today it's an
ugly five-input Alteryx build (the tool can't hold a variable for the moving column position) and the
"format" is a manual Format-Painter copy.

**The bar they'll judge on:** no code / accessible · trustable (**see & change the logic on the canvas**) ·
a colleague can co-own it · scheduled + audited · handles the missing workbook · **each account nets to
zero** with exceptions flagged · formatted Excel out.

### ② The story you tell while building
*"You drop your rolling cash-flow file — the one you carry forward. This month's account numbers are
already here as a simple table, and you can see exactly which workbook each figure came from. We join
them, reconcile, and hand you back a formatted Excel. No code, nothing re-keyed."* Keep it familiar —
**you drop a file**, like today — and lean on **provenance** (⑤) so nothing feels like a black box.

### ③ Build the flow — no code, all visual operators (7 boxes)
Every step is a **click** or a line of **plain English** — you never open a code box.
1. **Source ① — drop the Excel:** drag your rolling file **`rolling/CashFlowRec_2026-06.xlsx`** onto the
   canvas (the ONE file). *(A `.csv` sits beside it if you'd rather drop csv.)*
2. **Source ② — add this month's numbers** (the table `cf_period_extract`). *(Reassure the room: this isn't
   a robot changing your figures — it's just this month's workbook cells read in for you, and a
   **`source_file`** column shows the exact workbook each number came from. Show ⑤ here if they look uneasy.)*
3. **Join** — pick the key `account_code`, choose **Left** (keep every account).
4. **Prepare → Formula** — add **`Jul_Status`**: type the plain-English description *"Reconciled when the
   Control figure is zero, otherwise Exception"* and Designer fills it in. **No code box** — it's the same
   Reconciled/Exception rule you'd write by hand, and you can read it back in plain words.
5. **Select** — rename `current_period` → **`Jul_Current`** and `period_control` → **`Jul_Control`** (a
   rename field per column — pure clicks); untick the columns you don't want to carry.
6. **Sort** — Exception rows to the top.
7. **Output** → name it `cf_cashflow_rec_designer` → **Run.**

Seven boxes, all clicks and plain English. **The canvas *is* the logic** — to change a rule you edit the
box, in words, in front of them. That's the "trustable, not a black box" answer: they can see it and
change it, live, without code.

*Faster still — **one ✨ Generate prompt** builds the whole flow.* On a blank **+ New → Data prep** canvas,
type this in plain English:
> *Join the rolling cash-flow file to cf_period_extract on account_code, keeping every account (left join).
> Add a column Jul_Status that says "Reconciled" when the control figure is 0, otherwise "Exception".
> Rename current_period to Jul_Current and period_control to Jul_Control. Sort Exception rows to the top.
> Save it as cf_cashflow_rec_designer.*

Set the Output, **Run**. You typed a sentence; Designer built the flow.

### ④ Prove it — reconciliation on the canvas, Excel from a download
**Never say "notebook", never open code.** The two things you show:
- **The reconciliation is already done on the canvas** — the **`Jul_Status`** column reads Reconciled /
  Exception per account (**5 of 6 reconciled; ACC-003 is the exception**). No extra step — it's in the flow.
  Open the finished result as a grid: [`cf_cashflow_rec`](https://fevm-lr-dev-aws-us.cloud.databricks.com/explore/data/lr_dev_aws_us_catalog/designer_recon_demo/cf_cashflow_rec).
- **Get the Excel:** the reconciled result **downloads straight to Excel/CSV** (a standard download button),
  and the scheduled run drops the same formatted file in your folder:
  [`uc1/output/`](https://fevm-lr-dev-aws-us.cloud.databricks.com/explore/data/volumes/lr_dev_aws_us_catalog/designer_recon_demo/recon_landing). **No formatting to hand-do.**
- *"Each account's Control nets to zero — that's the reconciliation; the one that doesn't is flagged."*
  *(Frame the exception as a win: it's the tool doing your checking, not breaking. Nobody broke month-end.)*

> **If asked "is there code or a notebook behind this?"** — *"No. The logic is the visual flow you just
> watched; the Excel is a standard download, like Save As. There's nothing hand-written for anyone to
> maintain."* *(We do separately double-check every figure to the penny — that's our own quality check, kept
> out of the room. Mention it only if a skeptic pushes; there's nothing to open.)*

### ⑤ Provenance & audit — a spreadsheet grid, not a report to decode
- **Where every figure came from:** open [`cf_period_extract`](https://fevm-lr-dev-aws-us.cloud.databricks.com/explore/data/lr_dev_aws_us_catalog/designer_recon_demo/cf_period_extract)
  — the **`source_file`** column shows each account's exact workbook (and the missing one shows the fallback).
- **What the run did:** open [`cf_ingest_log`](https://fevm-lr-dev-aws-us.cloud.databricks.com/explore/data/lr_dev_aws_us_catalog/designer_recon_demo/cf_ingest_log)
  — one row per file, **ok** or **FAILED**. Nothing silently read.
- **Who changed the figures, when:** on any table, click the **History** tab in Catalog Explorer — a simple
  panel listing every version, timestamp and user. That's the auditor answer, as a screen they can read.

### ⑥ When they attack — the hard cases (all real, on tap)
- **"What about a bad file?"** Drop a corrupt workbook in the folder and re-run → it's logged **FAILED** and
  quarantined; the other accounts still process. (Proven.)
- **"A missing workbook?"** The missing account uses the **2-cell fallback** (visible in `source_file`).
- **"Does it roll across the year?"** The rolling file already carries **Apr / May / Jun** and you just
  appended **Jul** — one column-pair per period. Next month appends Aug; at month 12 a new FY file starts.
- **"Six accounts isn't my 200."** *Show it, don't tell it:* set the account count higher and re-run live —
  same flow, same result, more rows. It's **serverless / scale-to-zero** (pay for the run, not idle desktops).
- **"This is lock-in."** The opposite: your **Excel/CSV stay in your own folders**, and everything runs on
  **open file formats you can take with you** — nothing is trapped in a proprietary file you can't open
  without the tool. You can walk away with your data any day.

### ⑦ Collaborate & schedule (live, one click each)
- **Co-own it:** **Share → Can Edit** — two people on the *same* governed flow, every change tracked
  (vs emailing `final_v7.xlsx`).
- **Schedule + run history:** set the flow to run on a **schedule** and show the **run history** — it runs
  unattended, with no licensed user in the loop.

### ⑧ Only if pushed on the automation — keep it reassuring
*"Your workbooks land in the same folder you use today; the platform reads them so you don't re-key — and
you can see exactly what it used (⑤) and that nothing failed."* It's a convenience with full visibility,
**not** a black box that took your files away.

### Assets — kept deliberately small (6 accounts; scale up if they ask)
Folder [`recon_landing/uc1/`](https://fevm-lr-dev-aws-us.cloud.databricks.com/explore/data/volumes/lr_dev_aws_us_catalog/designer_recon_demo/recon_landing) — a few examples, **xlsx and csv**:
- **drag this →** `rolling/CashFlowRec_2026-06.xlsx` (also `.csv`) · account workbooks → `bank_recs/` ·
  the missing-account fallback → `fallback/` · **Excel/CSV output →** `output/` (standard download, no formatting to do)

Tables (open as grids): [`cf_prior_rec`](https://fevm-lr-dev-aws-us.cloud.databricks.com/explore/data/lr_dev_aws_us_catalog/designer_recon_demo/cf_prior_rec) (rolling) ·
[`cf_period_extract`](https://fevm-lr-dev-aws-us.cloud.databricks.com/explore/data/lr_dev_aws_us_catalog/designer_recon_demo/cf_period_extract) (this month, with `source_file`) ·
[`cf_cashflow_rec`](https://fevm-lr-dev-aws-us.cloud.databricks.com/explore/data/lr_dev_aws_us_catalog/designer_recon_demo/cf_cashflow_rec) (result) ·
[`cf_ingest_log`](https://fevm-lr-dev-aws-us.cloud.databricks.com/explore/data/lr_dev_aws_us_catalog/designer_recon_demo/cf_ingest_log) (ok/FAILED per file).

---

# UC2 — Control sheet

### ① The requirement — what they asked for (say this)
Two datasets: a **payments** sheet and a **supplier → category** lookup. **Look up** the category onto
each payment, **split into the six-or-seven groups** they report by (category + company + image group),
and a **control sheet** that **sums each group** — and the parts must **tie back to the whole with 0.00
variance**. That tie-back *is* the control.

**The bar:** no code / accessible · trustable + proof · co-own · scheduled + audited · Excel in / out ·
the parts tie to the whole.

### ② The story you tell
*"You drop your payments sheet and your category list; we look up each payment's category, group them the
way you report, and prove **every single payment** is accounted for and the groups add back to the total —
to the penny. Even a payment whose supplier isn't in the category list shows up as its own **Unmatched**
group, so the total is always the true whole. No code, nothing re-keyed."*

### ③ Build the flow — no code, all visual operators (very easy — here's exactly how)
**For a nervous room, lead with this — five boxes, all clicks and plain English:**
1. **Source ① — drop `inputs/Payments.xlsx`.**  2. **Source ② — drop `inputs/CategoryLookup.xlsx`.** *(both files; csv beside each.)*
3. **Join** — drop a **Join**, wire both in, pick `supplier` on each side, choose **Left join** — *"keep
   every payment; never drop one just because its category is missing."*
4. **Add the `branch` group** — drop a **Prepare → Formula** and type it in plain English:
   *"if the category is empty, call it 'Unmatched (no category)', otherwise the company code, then Provider
   if the category is Claims/Refund/Travel else NonProvider, then Img2 if account_id is even else Img3."*
   Designer fills it in — **no code box.**
5. **Total each group** — drop an **Aggregate** → group by `branch` → sum `amount_paid` → `branch_total`.
6. **Output** → `cs_control_sheet_designer` → **Run.**

Five boxes, each a click or a plain-English line. The grand total and the tie-back are the **check** in ④,
so you never hand-build a total row that could drift.

*The shortcut — **one ✨ prompt** builds the same flow.* On a blank **+ New → Data prep** canvas, type:
> *Join Payments to CategoryLookup on supplier, keeping every payment (left join). Add a branch column: if
> there's no category call it "Unmatched (no category)", otherwise the company code, then "Provider" when
> the category is Claims, Refund or Travel and "NonProvider" otherwise, then "Img2" when account_id is even
> and "Img3" otherwise. Group by branch and total amount_paid. Save it as cs_control_sheet_designer.*

Set the Output, **Run**. Same result — a sentence in, a flow out.

### ④ Prove it — the tie-back as a spreadsheet grid (the beat that wins the room)
**Open [`cs_population_recon`](https://fevm-lr-dev-aws-us.cloud.databricks.com/explore/data/lr_dev_aws_us_catalog/designer_recon_demo/cs_population_recon) as a grid — a simple table, not code.** It doesn't just flash "0.00"; it proves the
total is the **whole population**:
- **Every payment accounted for:** `400 in = 392 matched + 8 unmatched` — **0 dropped**.
- **No double-counting:** rows after the join = 400; **0 duplicate suppliers** — **0 fan-out**.
- **Groups sum to all payments:** Σ groups = Σ all = **−322,322.44**, **variance 0.00** — including Unmatched.
- The run **stops itself** if the control ever breaks — so it can't silently go wrong.
- **Excel out:** the control sheet **downloads to Excel/CSV** and the scheduled run drops it in
  [`uc2/output/`](https://fevm-lr-dev-aws-us.cloud.databricks.com/explore/data/volumes/lr_dev_aws_us_catalog/designer_recon_demo/recon_landing) — standard download, nothing to hand-format.

*"The one thing a control exists to catch — a missing or duplicated supplier quietly wrecking the total —
is exactly what this reconciles. Nothing hides behind a green 0.00."*

### ⑤ Trust & audit — all screens they can read
- **Lineage drill-through (Excel can't):** in Catalog Explorer, trace a group total → the aggregate → the
  join → the actual payment rows. Click a number, see the payments behind it.
- **The check is a gate, not decoration:** the tie-back **stops the run** if the control ever breaks.
- **See/change the logic:** it's the **visual flow** — edit a box in plain words. **Audit:** the table's
  **History** tab (who / when / what), a panel they can read.

### ⑥ When they attack — the hard cases (proven, not promised)
- **"Supplier not in the lookup?"** Shown live: **8** such payments land in the **Unmatched** group and stay
  in the total (392 + 8 = 400). Not dropped, not hidden.
- **"Duplicate-supplier double-count?"** The recon shows **rows-after-join = rows-in** and **0 duplicate
  suppliers** — a double-count stops the run.
- **"Eight groups isn't my dozens."** *Show it:* raise the payment count and re-run — same 0.00 tie-back at
  any scale, serverless / scale-to-zero.
- **"Your check marks its own homework."** Fair — so we'll **tie it to your exported control total, on your
  own file**, live.
- **"This locks me in."** No — Excel/CSV stay in **your folders**, on **open formats you can take with you**;
  nothing is trapped in a proprietary file.

### ⑦ Collaborate, schedule & reuse (live)
- **Share → Can Edit** — co-own the same flow, tracked. **Schedule** it with run history.
- **One definition, everywhere:** point **Genie** or an **AI/BI dashboard** at the control sheet. **If a
  technical/keen person is in the room, do it live** — ask *"Provider groups by company, largest first"* in
  plain English and let the answer come back off the same governed numbers. A 30-second move that turns an
  interested analyst into an advocate — don't leave it as a "next session" promise if you have the minute.

### Assets — small & legible (~400 payments → 8 groups + Unmatched)
Folder [`recon_landing/uc2/`](https://fevm-lr-dev-aws-us.cloud.databricks.com/explore/data/volumes/lr_dev_aws_us_catalog/designer_recon_demo/recon_landing) — **xlsx + csv**: drag `inputs/Payments.xlsx` **and**
`inputs/CategoryLookup.xlsx`; **output** in `output/`.
Tables (open as grids): [`cs_payments`](https://fevm-lr-dev-aws-us.cloud.databricks.com/explore/data/lr_dev_aws_us_catalog/designer_recon_demo/cs_payments) ·
[`cs_category_lookup`](https://fevm-lr-dev-aws-us.cloud.databricks.com/explore/data/lr_dev_aws_us_catalog/designer_recon_demo/cs_category_lookup) ·
[`cs_control_sheet`](https://fevm-lr-dev-aws-us.cloud.databricks.com/explore/data/lr_dev_aws_us_catalog/designer_recon_demo/cs_control_sheet) (result) ·
[`cs_population_recon`](https://fevm-lr-dev-aws-us.cloud.databricks.com/explore/data/lr_dev_aws_us_catalog/designer_recon_demo/cs_population_recon) (the tie-back).

---

# UC3 — Scheduled automation  *(started with a button, watched from a screen)*

### ① The requirement — what they asked for (say this)
Two jobs they run **by hand** today, on their desktop. The question they set: *"can the platform run and
log these on a schedule — unattended and audited?"* **Answer: yes — and you start it with a button and
watch it from a screen; there's nothing to open.**
- **3a — file staging:** files land in **two folders**; pick, per report code, the **correct version by
  file name** (not latest-arrived), and **copy** to a destination. No data change.
- **3b — daily BDX files:** monthly, run **all ~30** of last month's fixed-layout files → read each →
  **check each file balances** (its detail rows sum to its control row) → **consolidate** → log.

**The bar:** scheduled · unattended · **audited** · **every file accounted for** (nothing silently dropped,
mis-picked or mis-read) · runs like their job, but governed.

### ② The story you tell (governance over a desktop macro)
*"You already run these by hand. The difference: it fires the moment a file lands, it can't silently lose
or mis-read a file — every file gets a visible verdict — and the whole run is audited on the platform,
not on someone's laptop."* *(Reassure the nervous analyst: you still just drop the files, it runs itself,
and it hands you a plain summary — **you never open anything technical**. This is the part IT sets up once.)*

### ③ Run it with a button + the reconciliation that wins the room
**Press Run** on the two scheduled jobs (in **Workflows**) — no build, no code on screen. Then show the
**results as grids**:
- **3a — every file accounted for:** open [`af_version_audit`](https://fevm-lr-dev-aws-us.cloud.databricks.com/explore/data/lr_dev_aws_us_catalog/designer_recon_demo/af_version_audit)
  — each file marked **chosen / superseded / unrecognized**: **9 seen = 5 chosen + 4 superseded + 0
  unrecognized**, 5 copied. You *see* which version was picked and why the others weren't — nothing ignored.
- **3b — every file statused:** open [`fw_contra_log`](https://fevm-lr-dev-aws-us.cloud.databricks.com/explore/data/lr_dev_aws_us_catalog/designer_recon_demo/fw_contra_log)
  — each file **balances / doesn't balance / no control row / can't read / empty**, covering **every** file:
  **30 = 27 balanced + 2 not + 1 no control row**. A file that won't read is **flagged, never counted as
  zero**; a duplicate control row is **flagged, never double-counted**.
- **The point:** the **run history** + these audit grids = scheduled, unattended, **audited** — and it
  **fails loudly**, it never hides a bad file behind a green tick.

### ④ Trust & audit — the screens are the audit
- The status grids *are* the audit: who ran it (run history), which file was used/rejected and why
  (`af_version_audit`), which files didn't balance (`fw_contra_log`), plus each table's **History** tab.
- The checks are **gates** — the run **fails** if anything is unaccounted for, so the control can't
  silently pass.

### ⑤ When they attack — honest answers
- **"A bad file — no control row / empty / a mis-aligned line?"** Shown: flagged and **kept out of the
  totals**, not silently absorbed. (Proven.)
- **"Nobody's paged when it breaks."** The opposite: **failure alerts are built in** — email / Slack /
  PagerDuty on a failure (or on a check tripping), set with a click. You're *more* likely to know it broke
  than with a job on one laptop.
- **"A desktop tool already does this."** True for the middle; the platform adds **on-arrival triggering,
  a governed audit trail, the checks-as-gates, failure alerts, and no desktop dependency** — the same
  governed home as UC1/UC2.
- **Known edges — we'll be straight:** picking "the highest version by name" is a rule that a *re-issued*
  older file would need refining; single-file re-runs and very high volumes are standard patterns to add.
  We name these rather than pretend.

### Assets — kept small (2 folders / 5 codes; ~30 daily files)
Folder [`recon_landing/`](https://fevm-lr-dev-aws-us.cloud.databricks.com/explore/data/volumes/lr_dev_aws_us_catalog/designer_recon_demo/recon_landing): **3a** `uc3a/…` → `uc3a/destination`; **3b** `uc3b/incoming` →
`uc3b/output` (consolidated CSV + a plain run summary).
Tables (open as grids): [`af_version_audit`](https://fevm-lr-dev-aws-us.cloud.databricks.com/explore/data/lr_dev_aws_us_catalog/designer_recon_demo/af_version_audit) ·
[`af_files_staged`](https://fevm-lr-dev-aws-us.cloud.databricks.com/explore/data/lr_dev_aws_us_catalog/designer_recon_demo/af_files_staged) ·
[`fw_bdx_consolidated`](https://fevm-lr-dev-aws-us.cloud.databricks.com/explore/data/lr_dev_aws_us_catalog/designer_recon_demo/fw_bdx_consolidated) ·
[`fw_contra_log`](https://fevm-lr-dev-aws-us.cloud.databricks.com/explore/data/lr_dev_aws_us_catalog/designer_recon_demo/fw_contra_log).

**Closing line (only if time):** *same governed data → Genie + dashboard + forecasting = the next session.*

---

## Fallbacks — if short on time or it goes sideways
1. **✨ prompt** (③) — the no-code hero: one sentence builds the flow.
2. **Open the pre-saved flow** — if you built + Saved `Cash-flow rec — monthly` beforehand.
3. **Drag-drop by hand** — the seven boxes in ③.
4. **No live build at all** — open the finished result grids ([`cf_cashflow_rec`](https://fevm-lr-dev-aws-us.cloud.databricks.com/explore/data/lr_dev_aws_us_catalog/designer_recon_demo/cf_cashflow_rec),
   [`cs_population_recon`](https://fevm-lr-dev-aws-us.cloud.databricks.com/explore/data/lr_dev_aws_us_catalog/designer_recon_demo/cs_population_recon)) and the exported **Excel in the folder**. Still no code.

## Lines to land
1. *No code — you type plain English or drag boxes; you never see a line of code.*
2. *Everything starts and ends in Excel; the positional hack that made this "disgusting" is gone, and the Excel comes out from a standard download — nothing to hand-format.*
3. *It's reconciled to the penny, and the logic is right there on the canvas to see and change.*
4. *Nobody moves a file: it lands, and the work runs.*
5. *Nothing is hand-coded to maintain — the logic is the visual flow; there's no script anyone owns.*

---

> **Technical setup — one-time, before the session, NEVER opened in the room.** How the synthetic data is
> built, the behind-the-scenes checks that prove parity, and the rebuild steps live in **`docs/SETUP.md`**
> in the repository. None of it is part of the demo — the presenter does not open it during the session.
