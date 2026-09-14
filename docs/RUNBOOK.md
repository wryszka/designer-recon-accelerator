# Designer Recon Accelerator — Runbook (1-hour session)

A follow-along presenter guide for the **one-hour working session**: **Lakeflow Designer** led,
with **Excel at both ends**. Every file and table is named with its **exact location** and how to
open it. Read it top to bottom, click where it says, and the demo works.

> **About this demo.** All data is synthetic and fabricated — a representative finance / audit
> reconciliation estate. No customer data, organisation, bank, account or payee is real. A desktop
> ETL tool (Alteryx, Power Query, KNIME) is referenced as a familiar *workflow shape*, not a
> product comparison.

---

## 1. The story (what to land)
**Excel in → Designer in the middle → Excel out, and nobody moves a file.** Their work starts and
ends as Excel because that's what their teams and auditors need; Designer is the governed engine
between, and the moment a file lands the work runs.

Order for the hour (no minute-by-minute — keep it conversational):
1. **Cash-flow rec on Designer — the hero.** Excel workbooks + rolling Excel file in → append the
   two period columns no-code → **formatted Excel out automatically** (no Format Painter). The
   positional workaround the desktop tool forced simply doesn't exist here.
2. **Trust it & change it** — prompt-build, view/amend the code, co-edit, govern. Woven into 1 & 3.
3. **Control sheet on Designer** — split into ~6–7 category tables + a summary that sums each, ties
   back to the whole to the penny.
4. **Stop moving files** — a quick look at Autoloader + the automation jobs (5 minutes, not a chapter).
5. **Closing line only:** the same governed data answers plain-English questions (Genie), drives a
   dashboard, and forecasts — the next session.

---

## 2. Where everything lives (master reference)
Pre-built on the **DEV workspace**: `https://fevm-lr-dev-aws-us.cloud.databricks.com`

**Conventions:**
- **Notebook / file** → **Workspace → Shared → designer-recon-accelerator →** *folder* → open.
- **Table** → **Catalog → lr_dev_aws_us_catalog → designer_recon_demo →** *table* → **Sample data**.
- **Volume file** → same Catalog path → **Volumes → recon_landing**.
- **SQL warehouse** → the shared dev warehouse (`a3b61648ea4809e3`).

| Asset | Exact location |
|---|---|
| All notebooks | `/Workspace/Shared/designer-recon-accelerator/` |
| Catalog + schema (all tables) | `lr_dev_aws_us_catalog` → `designer_recon_demo` |
| Landing volume (UC1 workbooks + UC3 files) | Volume `recon_landing` |
| Jobs | Workflows → jobs prefixed `[recon-accel]` |
| Public repo | `https://github.com/wryszka/designer-recon-accelerator` |

**Key tables** (`lr_dev_aws_us_catalog.designer_recon_demo`):

| Table | Use case | What it holds |
|---|---|---|
| `cf_prior_rec`, `cf_period_extract` | UC1 | rolling baseline · this period parsed from the workbooks |
| `cf_benchmark`, `cf_cashflow_rec` | UC1 | parity oracle · the produced rec |
| `cs_payments`, `cs_category_lookup`, `cs_benchmark` | UC2 | sources · coded control sheet (oracle) |
| `af_files_staged`, `af_staging_audit` | UC3a | selected version per code · run log |
| `fw_bdx_consolidated`, `fw_contra_log` | UC3b | consolidated rows · per-file contra check |

**UC1 Excel files** — `recon_landing/uc1/`: `bank_recs/BankRec_*.xlsx` (the 17 workbooks),
`sap_fallback/` + `bank_fallback/` (missing-workbook fallback), `prior/CashFlowRec_2026-06.xlsx`
(rolling input), `output/CashFlowRec_2026-07.xlsx` (the **formatted output**).

---

## 3. Prerequisites — check tonight
- DEV workspace access, `lr_dev_aws_us_catalog` visible; a serverless **SQL warehouse**.
- **Lakeflow Designer (GA)** — confirm via **+ New → Data prep**.
- **⚠️ Excel file-format support ON** — the "drag an `.xlsx` onto the canvas" beat depends on it.
  **Test it tonight:** open a Data-prep canvas and drag `CashFlowRec_2026-06.xlsx` (download it from
  the Volume) onto it — it should create a Source. If it doesn't, enable *Excel File Format Support*
  in workspace settings (default-on since Jul 2026), or fall back to the pre-landed `cf_*` tables.
- **⭐ Build the UC1 flow once tonight and SAVE it.** While you're in there anyway: on a Data-prep
  canvas, paste the **UC1 prompt** (§ Fallbacks below), let Designer build it, set the Output table
  and **Run**, then **Save** the flow (name it `UC1 cash-flow rec`). That leaves a **ready flow in
  the workspace** you can open cold tomorrow if you run out of time. Do the same with the UC2 prompt
  if you want both saved. This is the single best insurance against the meeting going sideways.

---

## 4. Pre-flight — the morning of
1. **Confirm the data.** Catalog → `designer_recon_demo` → `cf_benchmark`, `cs_benchmark`,
   `fw_contra_log` exist. If empty, run the generators — §5.
2. **Open a blank Data-prep canvas once** so first load is instant.
3. **Dry-run the UC1 build once** (§6) — it's live clicks, no "Run all".
4. **Have the formatted output open** (`recon_landing/uc1/output/CashFlowRec_2026-07.xlsx`) to show
   the Excel that comes out.

---

## 5. Setup — it's built; here's how to (re)build it
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
**Different workspace / sandbox:** edit `databricks.yml` targets + `catalog_name`/`schema_name`;
every notebook has those widgets. Nothing else changes.

---

## 6. The demo — chapter by chapter

### 1 · Cash-flow rec on Designer — Excel in, Excel out *(the hero, ~half the session)*
Full detail: **demo_01_cashflow_rec → `README.md`**.
1. **Excel in.** On a blank **Data prep** canvas, **drag `CashFlowRec_2026-06.xlsx`** (from
   `recon_landing/uc1/prior/`) onto the canvas — Designer ingests the Excel and creates a Source.
   *(The per-workbook header-cell lift is done in `01`/`02` because it reads specific cells, not a
   table; `cf_period_extract` is that tidy result — add it as the second source.)*
2. **Append the two columns.** **Join** `cf_prior_rec` ← `cf_period_extract` on `account_code`;
   **SQL/select** to add `Jul_Current` and `Jul_Control` by name, keeping the prior columns. Point
   out: no positional maths, no five-input hack — you just add two named columns.
3. **Output** → table `cf_cashflow_rec_designer` → **Run**.
4. **One prompt instead:** the **✨ Generate** prompt in the folder README builds the whole flow.
5. **Excel out.** Show `02_parse_append_parity.py` has written the **formatted**
   `recon_landing/uc1/output/CashFlowRec_2026-07.xlsx` — navy header, currency formats, control
   breaks in red. *"That's the report, formatted, with no Format Painter."*
6. **Prove it:** run `02_parse_append_parity.py` → **✅ PARITY to the penny** vs `cf_benchmark`.

### 2 · Trust it & change it *(woven through 1 and 3)*
- **</> Code** toggle — the flow is real versioned SQL; hand it to an engineer who edits it, the
  change reflects back to the canvas.
- Catalog Explorer → `cf_cashflow_rec` → **Lineage**; **Schedule**; **Share → Can Edit** to co-own.

### 3 · Control sheet on Designer
Full detail: **demo_02_control_sheet → `README.md`**.
1. **Add source** → `cs_payments`, `cs_category_lookup`. **Join** on `supplier` (the lookup).
2. **SQL** to derive the branch key; **Aggregate** by branch → the 6–7 tables; **SQL** to add the
   `MAIN (all payments)` total + `variance`. **Output** → `cs_control_sheet` → **Run**.
3. **Prove it:** `02_parity.py` → **✅ PARITY**: the parts tie back to the whole with **0.00 variance**.

### 4 · Stop moving files *(a quick look — ~5 min)*
Full detail: **demo_03_automation → `README.md`**.
- **3a** `automation_file_staging` — files land in two folders; Autoloader sees them; the **right
  version per code** is selected **by name** and copied to a destination + `af_staging_audit`.
- **3b** `automation_bdx_parser` — ~30 fixed-width files parsed by position, **per-file contra
  check** (`fw_contra_log`: 28 tie, 2 don't), consolidated + a run summary.
- **The point:** Job run history + the log tables + lineage — scheduled, unattended, audited; no one
  moves a file by hand.

### 5 · Closing line (don't demo unless time)
*"The same governed data answers plain-English questions with Genie, drives a live dashboard, and
forecasts — that's the natural next session."*

---

## 6.5 Fallbacks — if you're short on time or the meeting turns
Customer meetings wander. Four layers, most-impressive first — drop down a layer whenever time or
the room demands it:

1. **Build live, drag-and-drop** (§6.1) — the full story.
2. **Build live from ONE prompt** — paste a prompt below into the canvas **✨ Generate** box;
   Designer builds the whole flow in seconds. Great when you want the "no-code" point without the
   click-by-click.
3. **Open the pre-saved flow** — if you built and Saved `UC1 cash-flow rec` tonight (§3), just open
   it and walk the finished canvas. Zero build risk.
4. **No Designer at all** — show the finished result and the Excel: `cf_cashflow_rec` (the produced
   rec), the formatted `recon_landing/uc1/output/CashFlowRec_2026-07.xlsx`, and run
   `02_parse_append_parity.py` for ✅ parity. The story still lands: Excel in, governed rec, Excel out.

**UC1 prompt** (paste into ✨ Generate):
> *Join cf_prior_rec to cf_period_extract on account_code, keeping all rows from cf_prior_rec. Add
> two new columns: Jul_Current from cf_period_extract.current_period, and Jul_Control from
> cf_period_extract.period_control. Keep every existing column of cf_prior_rec. Write the result to
> a table cf_cashflow_rec_designer in lr_dev_aws_us_catalog.designer_recon_demo.*

**UC2 prompt** (paste into ✨ Generate):
> *Join cs_payments and cs_category_lookup on supplier. Add a branch column = company_code + ' ' +
> (Provider if category in Claims/Refund/Travel else NonProvider) + ' ' + (Img2 if account_id is
> even else Img3). Aggregate: group by branch, sum amount_paid as branch_total. Then add a row
> labelled 'MAIN (all payments)' with the sum of all branch_totals and a variance column of 0.00.
> Write to a table cs_control_sheet in lr_dev_aws_us_catalog.designer_recon_demo.*

*(Both prompts are also in the per-UC folder READMEs. After a prompt build, set the Output table and
**Run**, then the matching `02_*` parity notebook proves it to the penny.)*

## 7. The lines to land
1. *Everything starts and ends in Excel — Designer is just the governed engine in the middle.*
2. *You append two named columns; the positional hack that made this "disgusting" doesn't exist — and
   the formatted Excel comes out automatically, no Format Painter.*
3. *You never read or trust the SQL blind — it's reconciled to the penny, and you can open and amend it.*
4. *Nobody moves a file: it lands, and the work runs.*

---

## 8. Troubleshooting
| Symptom | Fix |
|---|---|
| Can't drag an `.xlsx` onto the canvas | Enable Excel file-format support in workspace settings; or use the pre-landed `cf_*` tables. |
| Designer picker shows no tables | Point its catalog/schema at **lr_dev_aws_us_catalog / designer_recon_demo**. |
| `02_parity` says "canvas output pending" | Build the canvas first; set its Output table (UC2 `cs_control_sheet`). |
| `DELTA_METADATA_MISMATCH` on a log table | Stale table from an earlier schema — `DROP TABLE` it once; the notebooks recreate it. |
| Tables missing | Run the `[recon-accel]` jobs — §5. |

---

## 9. Running in a customer sandbox
`git clone`, edit `databricks.yml` targets, `databricks bundle deploy`, run the jobs, set each
notebook's `catalog_name` / `schema_name` widgets. All data is synthetic and generated in-place —
nothing customer-specific ever leaves.
