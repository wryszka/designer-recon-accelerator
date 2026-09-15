# Designer Recon Accelerator — Runbook (1-hour session)

A follow-along presenter guide for the **one-hour working session**: **Lakeflow Designer** led,
with **Excel at both ends**. Every source, join and output is spelled out — no cross-referencing.

> **About this demo.** All data is synthetic and fabricated — a representative finance / audit
> reconciliation estate. No customer data, organisation, bank, account or payee is real. A desktop
> ETL tool (Alteryx, Power Query, KNIME) is referenced as a familiar *workflow shape*, not a
> product comparison.

---

## 1. The story (what to land)
**Excel in → Designer in the middle → Excel out, and nobody moves a file.** Order for the hour:
1. **Cash-flow rec on Designer** — the hero (~half the session).
2. **Trust it & change it** — woven into 1 and 3 (prompt-build, view/amend code, co-edit, govern).
3. **Control sheet on Designer.**
4. **Stop moving files** — a 5-minute look at the scheduled automation (Jobs, not Designer).
5. **Closing line only:** same data → Genie + dashboard + forecasting = the next session.

---

## 2. Where everything lives
DEV workspace: `https://fevm-lr-dev-aws-us.cloud.databricks.com`
- **Tables** → **Catalog → `lr_dev_aws_us_catalog` → `designer_recon_demo` →** *table* → **Sample data**.
- **Volume files** → same path → **Volumes → `recon_landing`**.
- **Notebooks** → **Workspace → Shared → designer-recon-accelerator →** *folder*.
- **SQL warehouse** → shared dev warehouse `a3b61648ea4809e3`.

The tables each flow uses are listed inside its chapter below.

---

## 3. Check tonight / before the session
1. **Data is there:** Catalog → `designer_recon_demo` shows `cf_prior_rec`, `cf_period_extract`,
   `cs_payments`, `cs_category_lookup`. If not, run the generators — §7.
2. **Lakeflow Designer** available: **+ New → Data prep** opens a canvas.
3. **⚠️ Excel drag works:** drag `recon_landing/uc1/prior/CashFlowRec_2026-06.xlsx` onto a canvas —
   it should create a Source. If not, enable *Excel File Format Support* in workspace settings, or
   just use the `cf_prior_rec` table instead (same data).
4. **⭐ Build + SAVE the UC1 flow once now** (belt and braces): follow §5 below, then **Save** the
   flow as `Cash-flow rec — monthly`. Then you can open it cold tomorrow if you run out of time.

---

## 4. How Designer works (10-second orientation)
A flow is a left-to-right chain of **operators** you drop on the canvas and wire together:
**Source** (a table or file) → transforms → **Output** (writes a table). The transforms you'll see:
- **Join** — glue two sources together on a key.
- **Aggregate** — group + sum (like a pivot-table total).
- **SQL operator** — a box where you type an ordinary `SELECT`. "**Derive a column**" just means
  *add a new computed column* (e.g. add a `branch` column). You rarely type it by hand —

**the ✨ Generate prompt builds every operator for you.** For each chapter below, the fastest path is:
paste that chapter's prompt (§8) into the canvas **✨ Generate** box, hit go, set the Output table,
**Run**. The by-hand tables are there only if you want to click it yourself or explain a step.

---

## 5. Chapter 1 — Cash-flow rec on Designer  *(THE HERO)*

**Goal:** take last month's rolling file + this month's numbers → produce this month's rec with two
new columns → prove it to the penny → show the formatted Excel.

**Sources: 2.** ⚡ **Fastest path: paste the UC1 prompt (§8) into ✨ Generate — it builds this whole
flow. The table below is only if you want to click it by hand or explain a step.**

| # | Operator | Add / configure exactly this |
|---|---|---|
| 1 | **Source ①** | **Add source → `cf_prior_rec`** (catalog `lr_dev_aws_us_catalog`, schema `designer_recon_demo`). This is last month's rolling file: one row per account, columns `account_code`, `account_name`, `Apr_Current`, `Apr_Control`, `May_…`, `Jun_…`. |
| 2 | **Source ②** | **Add source → `cf_period_extract`** (same schema). This month's numbers: `account_code`, `current_period`, `period_control`, `source`. |
| 3 | **Join** | Add a **Join**; connect **①** and **②** into it. **Type = Left**, **left/primary = `cf_prior_rec`**, **key = `account_code` = `account_code`**. (20 rows each side, 1-to-1 → 20 rows out.) |
| 4 | **SQL operator** *(a box you type a SELECT in)* | After the join: **rename `current_period` → `Jul_Current`** and **`period_control` → `Jul_Control`**; **keep** all the prior columns; drop the duplicate `account_code` if it appears twice. |
| 5 | **Output** | **Output → new table `cf_cashflow_rec_designer`** (same catalog/schema) → **Run**. Result: last month's columns + the two new `Jul_` columns. |

> **Excel-in option (the "Designer eats Excel" beat):** instead of step 1, **drag
> `recon_landing/uc1/prior/CashFlowRec_2026-06.xlsx` onto the canvas** — Designer ingests the Excel
> and creates the *same* source as `cf_prior_rec`. It's a swap for source ①, **not a third source**.

**Trust & change it (do this here):**
- **</> Code** toggle — the flow is real, versioned SQL. Hand it to an engineer who tightens it; the
  edit reflects back into the canvas.
- Catalog Explorer → `cf_cashflow_rec_designer` → **Lineage**; **Schedule**; **Share → Can Edit** to co-own.

**Excel out:** open `recon_landing/uc1/output/CashFlowRec_2026-07.xlsx` — the formatted report the
job produced (navy header, currency formats, control breaks in red). *"That's the output, formatted,
no Format Painter."*

**Prove it:** run **`demo_01_cashflow_rec/02_parse_append_parity.py`** → **✅ PARITY to the penny**
vs `cf_benchmark`.

---

## 6. Chapter 3 — Control sheet on Designer

**Goal:** add category to the payments, split into the branch tables, and a summary that ties back to
the whole with 0.00 variance.

**Sources: 2.** ⚡ **Fastest path: paste the UC2 prompt (§8) into ✨ Generate — it builds this whole
flow. The table below is only if you want to click it by hand or explain a step.**

| # | Operator | Add / configure exactly this |
|---|---|---|
| 1 | **Source ①** | **Add source → `cs_payments`** (schema `designer_recon_demo`): the payment rows (`payment_doc_no`, `amount_paid`, `supplier`, `company_code`, `account_id`, …). |
| 2 | **Source ②** | **Add source → `cs_category_lookup`**: `supplier → category` (the VLOOKUP). |
| 3 | **Join** | Add a **Join**; connect **①** and **②**. **Type = Inner**, **key = `supplier` = `supplier`**. Name it **lookup category**. |
| 4 | **SQL operator** *(type a SELECT)* | It adds a `branch` column — name it **assign branch**: `SELECT *, concat(company_code, ' ', CASE WHEN category IN ('Claims','Refund','Travel') THEN 'Provider' ELSE 'NonProvider' END, ' ', CASE WHEN account_id % 2 = 0 THEN 'Img2' ELSE 'Img3' END) AS branch FROM lookup_category` |
| 5 | **Aggregate** | **Group by `branch`, SUM `amount_paid` → `branch_total`**. Name it **branch totals**. (These are your 6–7 category tables.) |
| 6 | **SQL operator** *(type a SELECT)* | Adds the MAIN total row + a 0.00 variance column — name it **control sheet**: `SELECT branch, round(branch_total,2) AS branch_total, 0.00 AS variance FROM branch_totals UNION ALL SELECT 'MAIN (all payments)', round(sum(branch_total),2), 0.00 FROM branch_totals` |
| 7 | **Output** | **Output → table `cs_control_sheet`** → **Run**. |

**Prove it:** run **`demo_02_control_sheet/02_parity.py`** → **✅ PARITY**: every branch matches, and
the parts tie back to the whole with **0.00 variance**.

---

## 7. Chapter 4 — Stop moving files  *(NOT a Designer flow — a scheduled Job)*

There is **no canvas and no sources** here — this is file/OS work, so it's a **Lakeflow Job**, and
that's the honest point: *Designer is for the transforms; scheduling + audit come from the platform.*
Run the two notebooks (or their jobs) and show the outputs — ~5 minutes total:

- **File staging** — `demo_03_automation/01_file_staging.py` (job `automation_file_staging`): files
  land in two folders, Autoloader sees them, the **right version per code is picked by name** and
  copied to a destination. Show `af_files_staged` + `af_staging_audit`.
- **Fixed-width / contra** — `demo_03_automation/02_fixedwidth_parser.py` (job
  `automation_bdx_parser`): ~30 fixed-width files parsed by position, **per-file contra check**
  (`fw_contra_log`: 28 tie, 2 don't), consolidated into `fw_bdx_consolidated` + a run summary.
- **The point:** Job **run history** + the log tables + **Lineage** = scheduled, unattended, audited.
  Nobody moves a file by hand.

**Closing line (don't demo unless time):** *"The same governed data answers plain-English questions
with Genie, drives a live dashboard, and forecasts — that's the natural next session."*

---

## 8. Fallbacks — if you're short on time or the meeting turns
Four layers, most-impressive first; drop a rung as needed:
1. **Build live** (§5 / §6).
2. **Build from ONE prompt** — paste a prompt below into the canvas **✨ Generate** box; Designer
   builds the whole flow in seconds.
3. **Open the pre-saved flow** — if you Saved `Cash-flow rec — monthly` (§3.4), just open and walk it.
4. **No Designer at all** — show `cf_cashflow_rec` + the formatted `CashFlowRec_2026-07.xlsx` + run
   `02_parse_append_parity.py` for ✅ parity. Story still lands: Excel in, governed rec, Excel out.

**UC1 prompt** (✨ Generate):
> *Join cf_prior_rec to cf_period_extract on account_code, keeping all rows from cf_prior_rec. Add two
> new columns: Jul_Current from cf_period_extract.current_period, and Jul_Control from
> cf_period_extract.period_control. Keep every existing column of cf_prior_rec. Write to a table
> cf_cashflow_rec_designer in lr_dev_aws_us_catalog.designer_recon_demo.*

**UC2 prompt** (✨ Generate):
> *Join cs_payments and cs_category_lookup on supplier. Add a branch column = company_code + ' ' +
> (Provider if category in Claims/Refund/Travel else NonProvider) + ' ' + (Img2 if account_id is even
> else Img3). Aggregate: group by branch, sum amount_paid as branch_total. Then add a row labelled
> 'MAIN (all payments)' with the sum of all branch_totals and a variance column of 0.00. Write to a
> table cs_control_sheet in lr_dev_aws_us_catalog.designer_recon_demo.*

---

## 9. The lines to land
1. *Everything starts and ends in Excel — Designer is just the governed engine in the middle.*
2. *You add two named columns; the positional hack that made this "disgusting" doesn't exist — and the
   formatted Excel comes out automatically, no Format Painter.*
3. *You never trust the SQL blind — it's reconciled to the penny, and you can open and amend it.*
4. *Nobody moves a file: it lands, and the work runs.*

---

## 10. Setup / (re)build the data
CLI authenticated to profile `DEV`:
```bash
git clone https://github.com/wryszka/designer-recon-accelerator.git
cd designer-recon-accelerator
databricks bundle deploy -t dev -p DEV
databricks bundle run generate_cashflow_rec     -t dev -p DEV   # cf_* + UC1 Excel files
databricks bundle run uc1_parse_append_parity   -t dev -p DEV   # parse → append → parity → Excel
databricks bundle run generate_control_sheet    -t dev -p DEV   # cs_*
databricks bundle run automation_file_staging   -t dev -p DEV   # af_* (UC3a)
databricks bundle run automation_bdx_parser     -t dev -p DEV   # fw_* (UC3b)
```

## 11. Troubleshooting
| Symptom | Fix |
|---|---|
| Can't drag an `.xlsx` onto the canvas | Enable Excel file-format support in workspace settings; or use the `cf_prior_rec` table. |
| Designer source picker shows no tables | Point its catalog/schema at **lr_dev_aws_us_catalog / designer_recon_demo**. |
| `02_parity` says "canvas output pending" | Build the canvas first and set its Output table. |
| `DELTA_METADATA_MISMATCH` on a log table | Stale table from an earlier schema — `DROP TABLE` it once; the notebook recreates it. |
| Tables missing | Run the `[recon-accel]` jobs — §10. |

*Running in a customer sandbox: `git clone`, edit `databricks.yml` targets, `bundle deploy`, run the
jobs, set each notebook's `catalog_name`/`schema_name` widgets. All data synthetic, generated in-place.*
