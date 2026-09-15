# Designer Recon Accelerator — Runbook (1-hour session)

Presenter guide for the one-hour session: **Lakeflow Designer**, **no code**, **Excel in and out**.
**Nothing you open in this session is code** — only a spreadsheet-style grid, an Excel file, or the visual
canvas. Three use cases.

> **About this demo.** All data is synthetic. No real organisation, bank, account or payee. A desktop
> ETL tool (Alteryx / Power Query / KNIME) is a *workflow shape*, not a product comparison.

**Say this in the first 20 seconds** (the reassurance that stops the nervous analyst fighting):
*"You still drop your file, exactly like today. A formatted Excel still comes out the other end. And you
can always tie the answer back to your own spreadsheet — nothing is hidden, nothing is taken away from you."*

## The arc of the session — say this so they see where it's going
**We don't ask you to change how you work. We start with your process, then make it easier, then show you
things you simply can't do today.**
1. **Your process today — on Databricks.** The exact steps you run now (drop the file, reconcile, Excel
   out) — just on the platform instead of a desktop, and with no code.
2. **Now make it smoother — Auto Loader.** Stop hunting for and moving files: they land in your folder and
   get picked up for you. *(You can still drop a file by hand — this is an option, not a takeaway.)*
3. **What you can't do today** — **governance** (who changed what, where every figure came from),
   **sharing** (two people co-owning the same work), and **versioning + previous runs** (every past run and
   result kept). This is the payoff, and it's all on screens they can read — never code.

**No-code, two ways:**
- **Type one plain-English instruction** into the canvas **✨ Generate** box → Designer builds the flow, **or**
- **drag-drop operators** (Source, Join, Aggregate, Output) and configure them by clicking.

The only thing you ever type is **plain English**. **There is no code, no SQL, and no script anywhere in
this session.** *(The synthetic data was built once before the room by a technical setup you never open —
see the last line.)*

**Everything opens from here — all no-code surfaces:**
- **Tables (open as spreadsheet-style grids):** https://fevm-lr-dev-aws-us.cloud.databricks.com/explore/data/lr_dev_aws_us_catalog/designer_recon_demo
- **Files (Excel in / out, the `recon_landing` folder):** https://fevm-lr-dev-aws-us.cloud.databricks.com/explore/data/volumes/lr_dev_aws_us_catalog/designer_recon_demo/recon_landing
- **Jobs — how to find *our* jobs among the hundreds:** in **Workflows** (left nav), type **`recon-accel`** in
  the search box. **All eight demo jobs carry the `[recon-accel]` prefix and nothing else does** — so you see
  exactly ours. Direct links are given at each step below.

**UC1 is the hero — it walks the full arc.** UC2 adds the one proof they can't do today; UC3 is the
automation they can't do today.

---

# UC1 — Cash-flow reconciliation  *(the hero, ~half the session — walks the whole arc)*

> **You asked** (from your requirements): *"can we read the header cells from each bank-rec workbook and
> append this period's two columns onto the rolling file — without Alteryx's positional hack — with every
> account netting to zero, exceptions flagged, and a formatted Excel out?"* **This is how we tackle it.**

### ① The requirement — what they do today (say this to walk them through it)
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

---

## Act 1 — your process today, on Databricks (no code)

### The story you tell while building
*"This is exactly what you do now — you drop your rolling cash-flow file, this month's account numbers come
in, we append the two columns and reconcile, and you get a formatted Excel back. Same steps, no desktop
tool, and not a line of code."* Keep it familiar — **you drop a file**, like today.

### Build the flow — all visual operators (7 boxes)
Every step is a **click** or a line of **plain English** — you never open a code box.
1. **Source ① — drop the Excel:** drag your rolling file **`rolling/CashFlowRec_2026-06.xlsx`** onto the
   canvas (the ONE file). *(A `.csv` sits beside it if you'd rather drop csv.)*
2. **Source ② — add this month's numbers** (the table `cf_period_extract`).
3. **Join** — pick the key `account_code`, choose **Left** (keep every account).
4. **Prepare → Formula** — add **`Jul_Status`**: type the plain-English description *"Reconciled when the
   Control figure is zero, otherwise Exception"* and Designer fills it in. **No code box** — it's the same
   Reconciled/Exception rule you'd write by hand, and you can read it back in plain words.
5. **Select** — rename `current_period` → **`Jul_Current`** and `period_control` → **`Jul_Control`** (a
   rename field per column — pure clicks); untick the columns you don't want to carry.
6. **Sort** — Exception rows to the top.
7. **Output** → name it `cf_cashflow_rec_designer` → **Run.**

Seven boxes, all clicks and plain English. **The canvas *is* the logic** — to change a rule you edit the
box, in words, in front of them.

*Faster still — **one ✨ Generate prompt** builds the whole flow.* On a blank **+ New → Data prep** canvas:
> *Join the rolling cash-flow file to cf_period_extract on account_code, keeping every account (left join).
> Add a column Jul_Status that says "Reconciled" when the control figure is 0, otherwise "Exception".
> Rename current_period to Jul_Current and period_control to Jul_Control. Sort Exception rows to the top.
> Save it as cf_cashflow_rec_designer.*

### Prove it — reconciliation on the canvas, formatted Excel out
- **The reconciliation is already done on the canvas** — the **`Jul_Status`** column reads Reconciled /
  Exception per account (**5 of 6 reconciled; ACC-003 is the exception**). Open **your flow's own output**
  `cf_cashflow_rec_designer` as a grid. *(If you didn't build live, the pre-built [`cf_cashflow_rec`](https://fevm-lr-dev-aws-us.cloud.databricks.com/explore/data/lr_dev_aws_us_catalog/designer_recon_demo/cf_cashflow_rec)
  twin holds the same result.)*
- **The formatted Excel is automatic** — a **formatted** `.xlsx` (bold headers, exceptions in red) **and** a
  `.csv` land in your folder, [`uc1/output/`](https://fevm-lr-dev-aws-us.cloud.databricks.com/explore/data/volumes/lr_dev_aws_us_catalog/designer_recon_demo/recon_landing).
  **The disgusting Format-Painter step is gone — the formatting comes out on its own.**
- *"Each account's Control nets to zero — that's the reconciliation; the one that doesn't is flagged."*
  *(Frame the exception as a win: it's the tool doing your checking, not breaking. Nobody broke month-end.)*

> **If asked "is there code or a notebook behind this?"** — *"No. The logic is the visual flow you just
> watched; the Excel comes out formatted on its own. There's nothing hand-written for anyone to maintain."*
> *(We do double-check every figure to the penny behind the scenes — our own QA, nothing to open. Mention
> only if a skeptic pushes.)*

---

## Act 2 — now make it smoother (Auto Loader)

*"You just dropped the file by hand — which is fine, you keep that. But you told us moving files around is
the painful bit. So instead: your workbooks **land in the folder and get picked up automatically** — no
hunting, no re-keying, no 'did I grab the right file'. You still see everything that came in."*
- The account numbers you added in Act 1 arrived this way — open [`cf_period_extract`](https://fevm-lr-dev-aws-us.cloud.databricks.com/explore/data/lr_dev_aws_us_catalog/designer_recon_demo/cf_period_extract)
  and show the **`source_file`** column: **you can see the exact workbook every figure came from** (and the
  missing account shows its fallback). Smoother, but you never lose sight of what was used.
- **Keep it reassuring:** *"It's a convenience with full visibility — not a black box that took your files
  away. Drop by hand or let it pick up; your call."*

---

## Act 3 — what you can't do today (the payoff — all screens, no code)

**1 · Governance — where every figure came from, and what the run did.**
- **Provenance:** the **`source_file`** column above — every number traceable to its workbook. Excel can't do that.
- **What the run read:** open [`cf_ingest_log`](https://fevm-lr-dev-aws-us.cloud.databricks.com/explore/data/lr_dev_aws_us_catalog/designer_recon_demo/cf_ingest_log)
  — one row per file, **ok** or **FAILED**. Nothing silently read; a bad file is quarantined, not skipped.
- *Optional, no-code:* ask **Genie** in plain English — *"show me any files that failed to load this month"* —
  and it answers off the same governed data. (Surface governance as a question, not a report to decode.)

**2 · Sharing — co-own the same work (talk track).**
*"Today this lives in one person's Alteryx and one person's Excel; you email `final_v7.xlsx` around. Here you
**Share → Can Edit** — two people on the **same** governed flow, at once, every change tracked. No more
'which copy is the real one'."*

**3 · Versioning + previous runs — nothing is ever lost.**
- **Every past run** is kept: open the backing job's **Runs** tab — `[recon-accel] UC1 parse → append → parity`
  → https://fevm-lr-dev-aws-us.cloud.databricks.com/jobs/129351423441855 → the **Runs** tab lists every past
  run (when, by whom, pass/fail).
- **Every past version of the result** is kept: on any table, click the **History** tab in Catalog Explorer
  — a simple panel of every version, timestamp and user. *"You can open last March's number as it stood then —
  try that with an overwritten spreadsheet."*

### When they attack — the hard cases (all real, on tap)
- **"What about a bad file?"** Drop a corrupt workbook and re-run → logged **FAILED** and quarantined; the
  other accounts still process. (Proven.)
- **"A missing workbook?"** The missing account uses the **2-cell fallback** (visible in `source_file`).
- **"Does it roll across the year?"** The rolling file already carries **Apr / May / Jun** and you just
  appended **Jul** — one column-pair per period; at month 12 a new FY file starts.
- **"Six accounts isn't my 200."** *Show it, don't tell it:* set the account count higher and re-run live —
  same flow, same result, more rows. **Serverless / scale-to-zero** (pay for the run, not idle desktops).
- **"This is lock-in."** The opposite: your **Excel/CSV stay in your own folders**, on **open file formats
  you can take with you** — nothing trapped in a proprietary file. Walk away with your data any day.

### Assets — kept deliberately small (6 accounts; scale up if they ask)
Folder [`recon_landing/uc1/`](https://fevm-lr-dev-aws-us.cloud.databricks.com/explore/data/volumes/lr_dev_aws_us_catalog/designer_recon_demo/recon_landing) — a few examples, **xlsx and csv**:
- **drag this →** `rolling/CashFlowRec_2026-06.xlsx` (also `.csv`) · account workbooks → `bank_recs/` ·
  the missing-account fallback → `fallback/` · **formatted Excel + CSV output →** `output/` (automatic, no Format-Painter)

Tables (open as grids): [`cf_prior_rec`](https://fevm-lr-dev-aws-us.cloud.databricks.com/explore/data/lr_dev_aws_us_catalog/designer_recon_demo/cf_prior_rec) (rolling) ·
[`cf_period_extract`](https://fevm-lr-dev-aws-us.cloud.databricks.com/explore/data/lr_dev_aws_us_catalog/designer_recon_demo/cf_period_extract) (this month, with `source_file`) ·
[`cf_cashflow_rec`](https://fevm-lr-dev-aws-us.cloud.databricks.com/explore/data/lr_dev_aws_us_catalog/designer_recon_demo/cf_cashflow_rec) (result) ·
[`cf_ingest_log`](https://fevm-lr-dev-aws-us.cloud.databricks.com/explore/data/lr_dev_aws_us_catalog/designer_recon_demo/cf_ingest_log) (ok/FAILED per file).

---

# UC2 — Control sheet  *(a task they do today + the one proof they can't do today)*

> **You asked:** *"can we look up a category onto each payment, split into the six-or-seven groups we report
> by, and produce a control sheet whose parts tie back to the whole at 0.00 variance?"* **This is how we tackle it.**

### ① The requirement — what they do today (say this)
Two datasets: a **payments** sheet and a **supplier → category** lookup. **Look up** the category onto
each payment, **split into the six-or-seven groups** they report by (category + company + image group, plus
an **Unmatched** catch-all), and a **control sheet** that **sums each group** — and the parts must **tie
back to the whole with 0.00 variance**. That tie-back *is* the control.

**The bar:** no code / accessible · trustable + proof · co-own · scheduled + audited · Excel in / out ·
the parts tie to the whole.

### Act 1 — your process today, on Databricks (no code)
*"You drop your payments sheet and your category list; we look up each payment's category, group them the
way you report, and hand you a formatted control sheet — same steps, no code."*

**Part 1 — the control sheet (five boxes, all clicks and plain English):**
1. **Source ① — drop `inputs/Payments.xlsx`.**  2. **Source ② — drop `inputs/CategoryLookup.xlsx`.** *(csv beside each.)*
3. **Join** — wire both in, pick `supplier` on each side, choose **Left join** — *"keep every payment; never
   drop one just because its category is missing."*
4. **Add the `branch` group** — drop a **Prepare → Formula**, in plain English: *"if the category is empty,
   call it 'Unmatched (no category)', otherwise the company code, then Provider if the category is
   Claims/Refund/Travel else NonProvider, then Img2 if account_id is even else Img3."* Designer fills it in.
5. **Total each group** — **Aggregate** → group by `branch` → sum `amount_paid` → `branch_total` →
   **Output** `cs_control_sheet_designer`. (A **formatted** control sheet lands in `uc2/output/` too.)

**Part 2 — build the tie-back on the SAME canvas** (so the proof comes *out of your flow*, not a table that
appears from nowhere — this is the beat that wins the room, and now it's connected):
6. **Grand total of the groups** — drop a second **Aggregate** reading the step-5 group totals, **no group
   key**, sum `branch_total` → `groups_total` (one number).
7. **Grand total of every payment** — drop an **Aggregate** reading the **Join** output (step 3), **no group
   key**, sum `amount_paid` → `all_total` (one number).
8. **Compare** — **Join** those two single rows, then **Prepare → Formula**: *"variance = groups_total minus
   all_total"* → **Output** `cs_tieback_designer`. **Variance = 0 → the parts tie to the whole, proven by the
   flow you built.**

*The shortcut — **one ✨ prompt** builds Part 1:*
> *Join Payments to CategoryLookup on supplier, keeping every payment (left join). Add a branch column: if
> there's no category call it "Unmatched (no category)", otherwise the company code, then "Provider" when
> the category is Claims, Refund or Travel and "NonProvider" otherwise, then "Img2" when account_id is even
> and "Img3" otherwise. Group by branch and total amount_paid. Save it as cs_control_sheet_designer.*

Then add Part 2's three boxes by hand (or tell ✨: *"also output the total of all payments, the total of the
group totals, and the difference between them"*).

### The proof you can't do today — parts = whole, from the flow you built (the beat that wins the room)
**Everything here comes out of the canvas you just built — no separate table appears from nowhere:**
- **Nothing dropped or duplicated:** on the **Join** node, the row count reads **400 in → 400 out** (the LEFT
  join keeps every payment; no supplier fans out). Point at it on the canvas.
- **Unmatched is visible:** the **8** no-category payments sit in their own **Unmatched (no category)** group in
  `cs_control_sheet_designer` — not dropped, not hidden.
- **Parts tie to the whole:** the **tie-back node** `cs_tieback_designer` (Part 2, steps 6–8) shows
  **Σ groups = Σ all payments = −322,322.44, variance 0.00.** The proof is a box in *your* flow.

*"The one thing a control exists to catch — a missing or duplicated supplier quietly wrecking the total — is
exactly what this flow proves, live, in front of you. Nothing hides behind a green 0.00, and nothing appears
from nowhere."*

> **Backstage only (never opened):** a coded check, `cs_population_recon`, computes this exact tie-back
> independently as *our* QA — the same numbers, proven a second way. Mention it to a skeptic; there's nothing
> to show on screen.

### What you can't do today (same three, briefly)
- **Governance / lineage — exact path:** open `cs_control_sheet_designer` in **Catalog Explorer → the
  `Lineage` tab**. The graph shows it traces back through the join to **`cs_payments`** and
  **`cs_category_lookup`**, and column lineage shows which source column fed each field. *To see the actual
  payments behind a group,* click the **Join step on the canvas** and use its data **preview** (filter to that
  branch), or ask **Genie** *"show the payments in the group I just clicked"*. *(There is no "click a cell →
  see rows" button — lineage for the trace, the canvas preview or Genie for the underlying rows.)*
- **Sharing:** **Share → Can Edit** — co-own the same flow, tracked.
- **Versioning + previous runs:** the backing job's **Runs** tab (`[recon-accel] UC2 build control sheet →
  parity`, https://fevm-lr-dev-aws-us.cloud.databricks.com/jobs/471464150602709) + the table's **History** tab —
  every past control sheet kept.
- **"Your check marks its own homework."** Fair — so we'll **tie it to your exported control total, on your
  own file**, live.

### Assets — small & legible (~400 payments → 8 groups incl. Unmatched)
Folder [`recon_landing/uc2/`](https://fevm-lr-dev-aws-us.cloud.databricks.com/explore/data/volumes/lr_dev_aws_us_catalog/designer_recon_demo/recon_landing) — **xlsx + csv**: drag `inputs/Payments.xlsx` **and**
`inputs/CategoryLookup.xlsx`; **formatted output** in `output/`.
Inputs (open as grids): [`cs_payments`](https://fevm-lr-dev-aws-us.cloud.databricks.com/explore/data/lr_dev_aws_us_catalog/designer_recon_demo/cs_payments) · [`cs_category_lookup`](https://fevm-lr-dev-aws-us.cloud.databricks.com/explore/data/lr_dev_aws_us_catalog/designer_recon_demo/cs_category_lookup).
**Your flow builds** `cs_control_sheet_designer` (group totals + Unmatched) and `cs_tieback_designer` (variance 0) — its own outputs, live.
*Backstage twins (fallback / our QA, not shown live):* [`cs_control_sheet`](https://fevm-lr-dev-aws-us.cloud.databricks.com/explore/data/lr_dev_aws_us_catalog/designer_recon_demo/cs_control_sheet) · [`cs_population_recon`](https://fevm-lr-dev-aws-us.cloud.databricks.com/explore/data/lr_dev_aws_us_catalog/designer_recon_demo/cs_population_recon).

---

# UC3 — Scheduled automation  *(the thing you can't do today — started with a button, watched from a screen)*

> **You asked:** *"can the platform run and log our two by-hand scripts on a schedule — pick the correct file
> version, contra-check each fixed-width file, and account for every file — unattended and audited?"* **This is
> how we tackle it.**

### ① The requirement — what they do today (say this)
Two jobs they run **by hand** today, on their desktop. The question they set: *"can the platform run and
log these on a schedule — unattended and audited?"* **Answer: yes — you start it with a button and watch
it from a screen; there's nothing to open. This is squarely the 'can't do today' part of the arc.**
- **3a — file staging:** files land in **two folders**; pick, per report code, the **correct version by
  file name** (not latest-arrived), and **copy** to a destination. No data change.
- **3b — daily BDX files:** monthly, run **all ~30** of last month's fixed-layout files → read each →
  **check each file balances** (its detail rows sum to its control row) → **consolidate** → log.

**The bar:** scheduled · unattended · **audited** · **every file accounted for** (nothing silently dropped,
mis-picked or mis-read) · runs like their job, but governed.

### ② The story (governance + Auto Loader, the two Act-2/Act-3 ideas made concrete)
*"You already run these by hand. The difference: it fires the moment a file lands (that's the Auto Loader
you saw), it can't silently lose or mis-read a file — every file gets a visible verdict — and the whole run
is audited on the platform, not on someone's laptop."* *(Reassure: you still just drop the files; it runs
itself and hands you a plain summary — **you never open anything technical**.)*

### ③ Run it with a button + the reconciliation that wins the room
**The two jobs — open each by its link and hit `Run now` (top-right), or in Workflows search `recon-accel`:**
- **3a — file staging:** `[recon-accel] UC3 file staging (Autoloader)` → https://fevm-lr-dev-aws-us.cloud.databricks.com/jobs/119422932361080
- **3b — fixed-width + contra:** `[recon-accel] UC3 fixed-width parser + contra` → https://fevm-lr-dev-aws-us.cloud.databricks.com/jobs/450258033805367

No build, no code on screen — you press **Run now** and watch. Then show the **grids**:
- **3a — every file accounted for:** [`af_version_audit`](https://fevm-lr-dev-aws-us.cloud.databricks.com/explore/data/lr_dev_aws_us_catalog/designer_recon_demo/af_version_audit)
  marks each file **chosen / superseded / unrecognized**: **9 seen = 5 chosen + 4 superseded + 0
  unrecognized**, 5 copied. You *see* which version was picked and why — nothing silently ignored.
- **3b — every file statused:** [`fw_contra_log`](https://fevm-lr-dev-aws-us.cloud.databricks.com/explore/data/lr_dev_aws_us_catalog/designer_recon_demo/fw_contra_log)
  — each file **balances / doesn't / no control row / can't read / empty**, covering **every** file:
  **30 = 27 balanced + 2 not + 1 no control row**. A file that won't read is **flagged, never counted as
  zero**; a duplicate control row is **flagged, never double-counted**.
- **The point:** **run history** + these audit grids = scheduled, unattended, **audited** — it **fails
  loudly**, never hiding a bad file behind a green tick.

### ④ What you can't do today, made concrete
- **Governance:** the status grids *are* the audit — who ran it (run history), which file was used/rejected
  and why, which didn't balance — plus each table's **History** tab. Auditors get a screen, not a black box.
- **Failure alerts are built in** — email / Slack / PagerDuty on a failure (or a check tripping), one click.
- **Versioning + previous runs:** every past run and its output kept and openable.

### ⑤ When they attack — honest answers
- **"A bad file — no control row / empty / a mis-aligned line?"** Flagged and **kept out of the totals**,
  not silently absorbed. (Proven.)
- **"A desktop tool already does this."** True for the middle; the platform adds **on-arrival triggering, a
  governed audit trail, checks-as-gates, failure alerts, and no desktop dependency**.
- **Known edges — we'll be straight:** "highest version by name" is a rule a *re-issued* older file would
  need refining; single-file re-runs and very high volumes are standard patterns to add. We name these.

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
1. **✨ prompt** (Act 1) — the no-code hero: one sentence builds the flow.
2. **Open the pre-saved flow** — if you built + Saved `Cash-flow rec — monthly` beforehand.
3. **Drag-drop by hand** — the seven boxes.
4. **No live build at all** — open the finished result grids ([`cf_cashflow_rec`](https://fevm-lr-dev-aws-us.cloud.databricks.com/explore/data/lr_dev_aws_us_catalog/designer_recon_demo/cf_cashflow_rec),
   [`cs_population_recon`](https://fevm-lr-dev-aws-us.cloud.databricks.com/explore/data/lr_dev_aws_us_catalog/designer_recon_demo/cs_population_recon)) and the **formatted Excel in the folder**. Still no code.

## Lines to land
1. *We start with your process — you don't have to change how you work; then we make it smoother; then we show you what you can't do today.*
2. *No code — you type plain English or drag boxes; you never see a line of code.*
3. *Everything starts and ends in Excel; the disgusting Format-Painter step is gone — the formatted Excel comes out on its own.*
4. *Governance, sharing and every past run are the things a desktop tool and a spreadsheet can't give you.*
5. *Nothing is hand-coded to maintain — the logic is the visual flow; there's no script anyone owns.*

---

> **Technical setup — one-time, before the session, NEVER opened in the room.** How the synthetic data is
> built, the behind-the-scenes checks that prove parity, the reusable Excel-formatting template, and the
> rebuild steps live in **`docs/SETUP.md`** in the repository. None of it is part of the demo.
