# Designer Recon Accelerator — Runbook (1-hour session)

Presenter guide: **Lakeflow Designer**, **no code**, **Excel in and out**. Everything you open is a
spreadsheet-style **grid**, an **Excel file**, or the **visual canvas** — never code.

> **About this demo.** All data is synthetic — no real organisation, account, or payee. A desktop ETL tool
> (Alteryx / Power Query / KNIME) is a *workflow shape*, not a product comparison.

**Open with (the reassurance that stops the nervous analyst fighting):** *"You still drop your file, exactly
like today. A formatted Excel still comes out. And you can always tie the answer back to your own spreadsheet."*

## The arc — say this so they see where it's going
**We don't ask you to change how you work.**
1. **Your process today, on Databricks** — the exact steps you run now, no desktop tool, no code.
2. **Smoother — Auto Loader** — files land in your folder and get picked up for you (still optional; you keep the file-drop).
3. **What you can't do today** — governance (where every figure came from), sharing (co-owning one flow), and versioning (every past run and result kept).

**No-code, two ways:** type one plain-English instruction into the canvas **✨ Generate** box, **or** drag-drop
operators (Source, Join, Aggregate, Output) and click to configure. You only ever type plain English — no SQL, no script.

**Everything opens from here:**
- **Tables (grids):** https://fevm-lr-dev-aws-us.cloud.databricks.com/explore/data/lr_dev_aws_us_catalog/designer_recon_demo
- **Files (`recon_landing`):** https://fevm-lr-dev-aws-us.cloud.databricks.com/explore/data/volumes/lr_dev_aws_us_catalog/designer_recon_demo/recon_landing
- **Jobs:** in **Workflows**, search **`recon-accel`** — all eight demo jobs carry that prefix and nothing else does. Direct links below.
- **Genie:** the space is **`Designer Recon — Finance`** → https://fevm-lr-dev-aws-us.cloud.databricks.com/genie/rooms/01f1b1409ffd17d29b5f0ebe339cb117 *(when a step says "ask Genie", this is it)*.

**UC1 is the hero and walks the whole arc.** UC2 adds the proof they can't do today; UC3 is the automation they can't do today.

---

# UC1 — Cash-flow reconciliation  *(the hero, ~half the session)*

> **You asked:** *"can we pull each account's reconciliation figures from its bank-rec workbook and append this
> period onto the rolling file — without Alteryx's positional hack — every account netting to zero, exceptions
> flagged, formatted Excel out?"* **This is how.**

### ① The requirement (say this)
Monthly, per bank account: read the account's **8 reconciliation lines** (opening/closing **O/S items** and
**balances per SAP and per Bank**) from its rec workbook's `Header` sheet, and **append this period's value +
control** as a new **`Period NN` pair** onto the **rolling file** (one pair per period; 12 periods, then a new
financial year). A missing workbook **falls back to 2 cells** from a separate SAP-balances file + bank statement.
Output a **formatted Excel**. Today it's an ugly five-input Alteryx build (no variable for the moving column) with
a manual Format-Painter step.

**The bar:** no-code · trustable (see & change the logic on the canvas) · co-ownable · scheduled + audited ·
handles the missing workbook · **each account nets to zero, exceptions flagged** · formatted Excel out.

## Act 1 — your process today, on Databricks
*"Same steps you run now — drop your rolling file, this period's figures come in, we append and reconcile, you
get a formatted Excel. No desktop tool, no code."*

**Build it — 7 visual boxes** (each a click or a plain-English line; you never open a code box):
1. **Source ① — drop the Excel:** drag `rolling/CashFlowRec_2026-06.xlsx` (a `.csv` sits beside it).
2. **Source ② — add this period's figures:** the table `cf_period_extract`.
3. **Join** on **`Account No.` + `Category`**, type **Left** (keep every line).
4. **Prepare → Formula — add `Status`:** *"on the Closing Balance per Bank line, Reconciled when the Control is 0, otherwise Exception"*. Designer fills it in — no code box.
5. **Select** — bring the new figures in as **`Period NN`** and **`Period NN Control`**; drop columns you don't need.
6. **Sort** — Exception rows to the top.
7. **Output** → `cf_cashflow_rec_designer` → **Run.**

**The canvas *is* the logic** — change a rule by editing the box, in words. *Faster: one ✨ Generate prompt on a
blank **+ New → Data prep** canvas:*
> *Join the rolling cash-flow file to cf_period_extract on Account No. and Category, keeping every row (left join).
> Add a Status column: on the "Closing Balance per Bank" line, "Reconciled" when the Control is 0 else "Exception".
> Bring current_period in as the new Period column and period_control as its Control. Sort Exception rows to the top.
> Save as cf_cashflow_rec_designer.*

### Prove it
- **Reconciliation is on the canvas** — the **`Status`** column reads Reconciled / Exception per account
  (**5 of 6 reconciled; account `0010003` is the exception**). Open **your own output** `cf_cashflow_rec_designer`
  as a grid *(or, if you didn't build live, the twin [`cf_cashflow_rec`](https://fevm-lr-dev-aws-us.cloud.databricks.com/explore/data/lr_dev_aws_us_catalog/designer_recon_demo/cf_cashflow_rec))*.
- **Formatted Excel is automatic** — a styled `.xlsx` (bold header, exception in red) + `.csv` land in
  [`uc1/output/`](https://fevm-lr-dev-aws-us.cloud.databricks.com/explore/data/volumes/lr_dev_aws_us_catalog/designer_recon_demo/recon_landing). The Format-Painter step is gone.
- *Frame the exception as a win — the tool did your checking; nobody broke month-end.*

> **"Is there code behind this?"** — *"No. The logic is the visual flow; the Excel comes out formatted on its own; nothing hand-written to maintain."* *(We double-check every figure to the penny backstage — our QA, nothing to open.)*

## Act 2 — smoother (Auto Loader)
*"Moving files is the painful bit — so your workbooks land in the folder and get picked up automatically. You
still see everything that came in."* Open [`cf_period_extract`](https://fevm-lr-dev-aws-us.cloud.databricks.com/explore/data/lr_dev_aws_us_catalog/designer_recon_demo/cf_period_extract)
and show **`source_file`** — every figure traces to the exact workbook (the missing account shows its fallback).
*Reassure: a convenience with full visibility, not a black box — drop by hand or let it pick up, your call.*

## Act 3 — what you can't do today (all screens, no code)
- **Governance:** `source_file` above traces every figure to its workbook; [`cf_ingest_log`](https://fevm-lr-dev-aws-us.cloud.databricks.com/explore/data/lr_dev_aws_us_catalog/designer_recon_demo/cf_ingest_log)
  logs each file **ok / FAILED** (a bad file is quarantined, not skipped). Or ask the **Genie**: *"any files that failed to load this month?"*
- **Sharing:** **Share → Can Edit** — two people on the *same* governed flow, every change tracked (vs emailing `final_v7.xlsx`).
- **Versioning + past runs:** the backing job's **Runs** tab (`[recon-accel] UC1 parse → append → parity` → https://fevm-lr-dev-aws-us.cloud.databricks.com/jobs/129351423441855) + any table's **History** tab — open last March's number as it stood.

### When they attack
- **Bad file?** Drop a corrupt workbook, re-run → logged **FAILED** and quarantined; others still process.
- **Missing workbook?** The **2-cell fallback** covers it (visible in `source_file`).
- **Roll across the year?** The rolling file carries the prior periods; you just appended this one; at period 12 a new FY file starts.
- **"6 accounts isn't my 200."** Raise the account count and re-run live — same flow, serverless / scale-to-zero.
- **"Lock-in."** Opposite — Excel/CSV stay in **your** folders, on open formats; nothing trapped.

### Assets (6 accounts, kept legible)
Folder [`recon_landing/uc1/`](https://fevm-lr-dev-aws-us.cloud.databricks.com/explore/data/volumes/lr_dev_aws_us_catalog/designer_recon_demo/recon_landing): drag `rolling/CashFlowRec_2026-06.xlsx`; workbooks in `bank_recs/`;
missing-account fallback in `fallback/`; formatted output in `output/`.
Grids: [`cf_prior_rec`](https://fevm-lr-dev-aws-us.cloud.databricks.com/explore/data/lr_dev_aws_us_catalog/designer_recon_demo/cf_prior_rec) (rolling, long: account × 8 lines) ·
[`cf_period_extract`](https://fevm-lr-dev-aws-us.cloud.databricks.com/explore/data/lr_dev_aws_us_catalog/designer_recon_demo/cf_period_extract) (this period + `source_file`) ·
[`cf_cashflow_rec`](https://fevm-lr-dev-aws-us.cloud.databricks.com/explore/data/lr_dev_aws_us_catalog/designer_recon_demo/cf_cashflow_rec) (result) ·
[`cf_ingest_log`](https://fevm-lr-dev-aws-us.cloud.databricks.com/explore/data/lr_dev_aws_us_catalog/designer_recon_demo/cf_ingest_log) (ok/FAILED).

---

# UC2 — Control sheet  *(a task they do today + the proof they can't)*

> **You asked:** *"look up a category onto each payment, split into the groups we report by, and a control sheet
> whose parts tie back to the whole at 0.00?"* **This is how.**

### ① The requirement (say this)
A **payments** sheet + a **supplier → category** lookup. Look up the category, split into the **6–7 groups** they
report by (category + company + image group, plus an **Unmatched** catch-all), sum each group in a **control
sheet**, and the parts must **tie back to the whole at 0.00**. That tie-back *is* the control.

### Act 1 — build it (5 boxes, all clicks + plain English)
1–2. **Source** — drop `inputs/Payments.xlsx` and `inputs/CategoryLookup.xlsx` (csv beside each).
3. **Join** on `supplier`, **Left** — *"keep every payment even if its category is missing."*
4. **Prepare → Formula — `branch`:** *"if category is empty, 'Unmatched (no category)', else company code, then Provider if category is Claims/Refund/Travel else NonProvider, then Img2 if account_id is even else Img3."*
5. **Aggregate** — group by `branch`, sum `amount_paid` → `branch_total` → **Output** `cs_control_sheet_designer` (formatted Excel lands in `uc2/output/`).

**Then build the tie-back on the SAME canvas** (so the proof comes out of *your* flow, not a table from nowhere):
6. **Aggregate** the step-5 totals (no group key) → `groups_total`.  7. **Aggregate** the Join output (no group key) sum `amount_paid` → `all_total`.  8. **Join** the two + **Formula** `variance = groups_total − all_total` → **Output** `cs_tieback_designer`. **Variance 0 = parts tie to the whole.**

*Shortcut — one ✨ prompt builds steps 1–5:*
> *Join Payments to CategoryLookup on supplier, keeping every payment (left join). Add a branch column: if there's
> no category "Unmatched (no category)", else company code, then "Provider" when category is Claims/Refund/Travel
> else "NonProvider", then "Img2" when account_id is even else "Img3". Group by branch, total amount_paid. Save as
> cs_control_sheet_designer.* *(Then add steps 6–8, or tell ✨ to also output the two grand totals and their difference.)*

### The proof you can't do today (the beat that wins the room)
All from the canvas you built:
- **Nothing dropped/duplicated:** the **Join** node reads **400 in → 400 out** (LEFT join keeps every payment; no fan-out).
- **Unmatched visible:** the **8** no-category payments sit in their own group in `cs_control_sheet_designer`.
- **Parts tie to whole:** `cs_tieback_designer` shows **Σ groups = Σ all = −322,322.44, variance 0.00**.

*"The one thing a control exists to catch — a missing or duplicated supplier wrecking the total — is exactly what this proves, live. Nothing hides behind a green 0.00."* *(Backstage QA twin, never shown: `cs_population_recon`.)*

### What you can't do today
- **Lineage:** open `cs_control_sheet_designer` → **Catalog Explorer → `Lineage` tab** → it traces back through the join to `cs_payments` and `cs_category_lookup`. For the rows behind a group, use the Join node's **preview** or ask the Genie. *(No "click a cell → rows" button.)*
- **Sharing:** **Share → Can Edit**.  **Versioning:** the backing job's **Runs** tab (`[recon-accel] UC2 build control sheet → parity` → https://fevm-lr-dev-aws-us.cloud.databricks.com/jobs/471464150602709) + the table's **History** tab.
- **"Marks its own homework?"** Fair — we'll **tie it to your exported control total, on your file**, live.

### Assets (~400 payments → 8 groups incl. Unmatched)
Folder [`recon_landing/uc2/`](https://fevm-lr-dev-aws-us.cloud.databricks.com/explore/data/volumes/lr_dev_aws_us_catalog/designer_recon_demo/recon_landing): drag `inputs/Payments.xlsx` + `inputs/CategoryLookup.xlsx`; formatted output in `output/`.
Grids: [`cs_payments`](https://fevm-lr-dev-aws-us.cloud.databricks.com/explore/data/lr_dev_aws_us_catalog/designer_recon_demo/cs_payments) · [`cs_category_lookup`](https://fevm-lr-dev-aws-us.cloud.databricks.com/explore/data/lr_dev_aws_us_catalog/designer_recon_demo/cs_category_lookup).
Your flow builds `cs_control_sheet_designer` + `cs_tieback_designer`. Backstage twins (fallback / QA): [`cs_control_sheet`](https://fevm-lr-dev-aws-us.cloud.databricks.com/explore/data/lr_dev_aws_us_catalog/designer_recon_demo/cs_control_sheet) · [`cs_population_recon`](https://fevm-lr-dev-aws-us.cloud.databricks.com/explore/data/lr_dev_aws_us_catalog/designer_recon_demo/cs_population_recon).

---

# UC3 — Scheduled automation  *(the thing you can't do today — start with a button, watch from a screen)*

> **You asked:** *"can the platform run and log our two by-hand jobs on a schedule — pick the correct file version,
> contra-check each fixed-width file, account for every file — unattended and audited?"* **This is how.**

### ① The requirement (say this)
Two jobs run by hand today. **Answer: yes — start with a button, watch from a screen, nothing to open.**
- **3a — file staging:** files land in **two folders**; per report code, pick the **correct version by the
  date-time stamp in the file name** (not latest-arrived), and **copy** to a destination. No data change.
- **3b — payment submissions:** monthly, fixed-width files from **two sources** → **parse by position** →
  **per-file contra** (detail rows **Trans Code 99** sum to the **Trans Code 17** contra row) → **consolidate**
  (tagged by source) → **log**.

**The bar:** scheduled · unattended · **audited** · **every file accounted for** (nothing silently dropped, mis-picked or mis-read).

### ② The story
*"You run these by hand now. Here it fires the moment a file lands, can't silently lose or mis-read one — every
file gets a visible verdict — and the whole run is audited on the platform, not a laptop. You never open anything technical."*

### ③ Run it + the reconciliation that wins the room
**Open each job and hit `Run now`** (or search `recon-accel` in Workflows):
- **3a:** `[recon-accel] UC3 file staging (Autoloader)` → https://fevm-lr-dev-aws-us.cloud.databricks.com/jobs/119422932361080
- **3b:** `[recon-accel] UC3 fixed-width parser + contra` → https://fevm-lr-dev-aws-us.cloud.databricks.com/jobs/450258033805367

Then show the **grids**:
- **3a — every file accounted for:** [`af_version_audit`](https://fevm-lr-dev-aws-us.cloud.databricks.com/explore/data/lr_dev_aws_us_catalog/designer_recon_demo/af_version_audit)
  marks each file **chosen / superseded / unrecognized**: **6 seen = 4 chosen + 2 superseded** (0 unrecognized), 4 copied. You see which version was picked and why.
- **3b — every file statused:** [`fw_contra_log`](https://fevm-lr-dev-aws-us.cloud.databricks.com/explore/data/lr_dev_aws_us_catalog/designer_recon_demo/fw_contra_log):
  **6 files = 3 MATCH + 1 MISMATCH + 1 NO CONTRA + 1 PARSE ISSUE**. A file that won't parse is **flagged, never summed as 0**; a duplicate contra row is **flagged, never double-counted**.
- **The point:** run history + these grids = scheduled, unattended, **audited** — it **fails loudly**, never hiding a bad file behind a green tick.

### ④ What you can't do today
- **Governance:** the status grids *are* the audit (who ran it, which file used/rejected and why, which didn't tie) + each table's **History** tab.
- **Failure alerts built in** — email / Slack / PagerDuty on failure or a check tripping, one click.

### ⑤ When they attack
- **Bad file (no contra / empty / mis-aligned)?** Flagged and kept out of the totals, not silently absorbed.
- **"A desktop tool already does this."** For the middle, yes — the platform adds on-arrival triggering, a governed audit trail, checks-as-gates, failure alerts, no desktop dependency.
- **Honest edges:** "correct version by name" needs a smarter rule for a re-issued older file; single-file re-runs and very high volumes are standard patterns to add.

### Assets
Folder [`recon_landing/`](https://fevm-lr-dev-aws-us.cloud.databricks.com/explore/data/volumes/lr_dev_aws_us_catalog/designer_recon_demo/recon_landing): **3a** `uc3a/sources/{folder_a,folder_b}` → `uc3a/destination`; **3b** `uc3b/incoming` → `uc3b/output` (consolidated CSV + run summary).
Grids: [`af_version_audit`](https://fevm-lr-dev-aws-us.cloud.databricks.com/explore/data/lr_dev_aws_us_catalog/designer_recon_demo/af_version_audit) · [`af_files_staged`](https://fevm-lr-dev-aws-us.cloud.databricks.com/explore/data/lr_dev_aws_us_catalog/designer_recon_demo/af_files_staged) · [`fw_bdx_consolidated`](https://fevm-lr-dev-aws-us.cloud.databricks.com/explore/data/lr_dev_aws_us_catalog/designer_recon_demo/fw_bdx_consolidated) · [`fw_contra_log`](https://fevm-lr-dev-aws-us.cloud.databricks.com/explore/data/lr_dev_aws_us_catalog/designer_recon_demo/fw_contra_log).

**Closing (if time):** *same governed data → Genie + dashboard + forecasting = the next session.*

---

## Fallbacks
1. **✨ prompt** — one sentence builds the flow.
2. **Pre-saved flow** — `Finance_Use_Case_1` (UC1), `Finance_Use_Case_2` (UC2).
3. **Drag-drop by hand** — the boxes above.
4. **No live build** — open the result grids ([`cf_cashflow_rec`](https://fevm-lr-dev-aws-us.cloud.databricks.com/explore/data/lr_dev_aws_us_catalog/designer_recon_demo/cf_cashflow_rec), [`cs_population_recon`](https://fevm-lr-dev-aws-us.cloud.databricks.com/explore/data/lr_dev_aws_us_catalog/designer_recon_demo/cs_population_recon)) + the formatted Excel in the folder.

## Lines to land
1. *We start with your process — you don't change how you work; then we make it smoother; then we show what you can't do today.*
2. *No code — plain English or drag boxes; you never see a line of code.*
3. *Everything starts and ends in Excel; the Format-Painter step is gone — formatted Excel comes out on its own.*
4. *Governance, sharing and every past run are what a desktop tool and a spreadsheet can't give you.*
5. *Nothing hand-coded to maintain — the logic is the visual flow.*

## Canvas vs notebook — the honest answer (keep for the room)
*"Why the canvas, not a notebook?"* For the reconciliation work — join, look up, derive, aggregate, tie back — the
**canvas** is the better choice: no code, self-documenting, easy to change and co-own, and **no loss of governance**
(same lineage, versioning, scheduling). A **notebook** earns its place only for what a picture can't draw — reading
Excel header cells, parsing fixed-width files, libraries/ML, unit tests, or plumbing (ingest, formatting, checks).
That's exactly this demo: the canvas does the business logic; hidden notebooks do only the rest. You start no-code
and drop to code for the ~5% that needs it — same platform, same governance. **One line:** *"Do the reconciliation
where you can see and change it; keep code for the parts a picture can't draw."*

---

> **Technical setup — one-time, before the session, NEVER opened in the room.** How the synthetic data is built,
> the backstage parity checks, the reusable Excel-formatting template, and the rebuild steps live in
> **`docs/SETUP.md`** in the repo. None of it is part of the demo.
