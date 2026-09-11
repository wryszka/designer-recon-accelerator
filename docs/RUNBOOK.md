# Designer Recon Accelerator — Runbook

A complete, follow-along guide to setting up and delivering this demo. Every file and every
table is named with its **exact location** and how to open it. Read it top to bottom, click
where it says, and the demo works.

> **About this demo.** All data is synthetic and fabricated — a representative finance / audit
> reconciliation estate. No customer data, organisation, bank, account or payee is real. A
> desktop ETL tool (Alteryx, Power Query, KNIME) is referenced as a familiar *workflow shape*,
> not a product comparison.

---

## 1. What this is
Three finance / audit workflows that teams run today in a desktop ETL tool plus Python, rebuilt
on Databricks. The thread that ties them together: the hard part is the **file interface** —
files landing in folders and formatted outputs going back out — not the logic in between.

- **UC1 — Cash-flow rec:** each month, read a few header cells from ~20 bank-rec workbooks and
  **append two new columns** (Current + Control) onto a rolling cash-flow file; missing workbooks
  fall back to two cells; **formatted Excel** out. **Lakeflow Designer.**
- **UC2 — Control sheet:** split payments into ~6–7 category tables; a summary control sheet sums
  them and ties back to the whole with **0.00 variance**. **Lakeflow Designer.**
- **UC3 — Scheduled automation:** 3a pick the right file version by name + copy + log; 3b parse
  ~30 fixed-width files, contra-check each against its contra row, consolidate + log. **Lakeflow
  Jobs + Autoloader + Unity Catalog audit** (not Designer — the honest answer to "can the platform
  schedule + log like our scripts?").

**The story:** *UC1 and UC2 are the desktop-ETL work — lookup, aggregate, reconcile — done
visually on a governed platform and reconciled to the penny. UC3 is the scheduling, autonomous
runs and audit trail the desktop tool can't give you. And on the Designer flows you never have to
read the SQL, nor trust it blindly — you tie it out.*

---

## 2. Where everything lives (master reference)
Pre-built on the **DEV workspace**: `https://fevm-lr-dev-aws-us.cloud.databricks.com`

**Conventions:**
- **Notebook / file** → left sidebar **Workspace → Shared → designer-recon-accelerator →** *folder* → open the file.
- **Table** → left sidebar **Catalog → lr_dev_aws_us_catalog → designer_recon_demo →** *table* → **Sample data** tab.
- **Volume file** → same Catalog path → **Volumes → recon_landing**.
- **SQL warehouse** → the shared dev warehouse (`a3b61648ea4809e3`); pick it under **Connect**.

| Asset | Exact location |
|---|---|
| All notebooks | Workspace → `/Workspace/Shared/designer-recon-accelerator/` |
| Catalog + schema (all tables) | `lr_dev_aws_us_catalog` → `designer_recon_demo` |
| Landing volume (UC1 workbooks + UC3 files) | Volume `recon_landing` |
| Jobs | Workflows → jobs prefixed `[recon-accel]` |
| Public repo | `https://github.com/wryszka/designer-recon-accelerator` |

**Tables** (all in `lr_dev_aws_us_catalog.designer_recon_demo`):

| Table | Use case | What it holds |
|---|---|---|
| `cf_accounts`, `cf_prior_rec`, `cf_period_extract` | UC1 | account ref · rolling baseline · this period parsed from files |
| `cf_benchmark` | UC1 | expected output (parity oracle) |
| `cf_cashflow_rec` | UC1 | the produced rolling rec (prior + the two new columns) |
| `cs_payments`, `cs_category_lookup` | UC2 | sources |
| `cs_benchmark` | UC2 | coded control sheet (parity oracle) |
| `cs_control_sheet` | UC2 | the table you build on the Designer canvas |
| `af_files_bronze`, `af_files_staged`, `af_staging_audit` | UC3a | files seen · selected version · run log |
| `fw_bdx_consolidated`, `fw_contra_log` | UC3b | consolidated detail rows · per-file contra check |

**UC1 Volume files** — `recon_landing/uc1/`: `bank_recs/` (workbooks), `sap_fallback/` +
`bank_fallback/` (missing-workbook fallback), `prior/` (last month's rolling file),
`output/CashFlowRec_<period>.xlsx` (the formatted output).

---

## 3. Prerequisites
- DEV workspace access with `lr_dev_aws_us_catalog` visible; a serverless **SQL warehouse**.
- **Lakeflow Designer (GA)** — confirm via **+ New → Data prep**. Needed for UC1 & UC2's live build.
- **Excel file-format support** enabled (default-on since Jul 2026) if you want to drag a raw
  `.xlsx` onto the canvas — worth a 2-minute check in the target workspace.
- To (re)deploy elsewhere: the **Databricks CLI**, authenticated.

---

## 4. Pre-flight — the day before
1. **Confirm the data.** Catalog → `designer_recon_demo` → check `cf_benchmark`, `cs_benchmark`
   and `fw_contra_log` exist. If the schema is empty, run the generators — §5.
2. **Open the surfaces once** so first load is instant: a blank **Data prep** canvas.
3. **Dry-run both Designer builds once** (UC1 §6, UC2 §6) — the canvas is live clicks, no "Run all".

---

## 5. Setup — it's built; here's how to (re)build it
On DEV (rebuild in place), CLI authenticated to profile `DEV`:
```bash
git clone https://github.com/wryszka/designer-recon-accelerator.git
cd designer-recon-accelerator
databricks bundle deploy -t dev -p DEV
databricks bundle run generate_cashflow_rec     -t dev -p DEV   # cf_* tables + UC1 Volume files
databricks bundle run uc1_parse_append_parity   -t dev -p DEV   # parse → append → parity → Excel
databricks bundle run generate_control_sheet    -t dev -p DEV   # cs_* tables
databricks bundle run automation_file_staging   -t dev -p DEV   # af_* tables (UC3a)
databricks bundle run automation_bdx_parser     -t dev -p DEV   # fw_* tables (UC3b)
```
**Different workspace / sandbox:** edit `databricks.yml` targets + `catalog_name`/`schema_name`;
every notebook also has those widgets at the top. Nothing else changes.

---

## 6. Chapter-by-chapter — the verbose steps

### UC1 · Cash-flow rec — Lakeflow Designer
Full click-through: **Workspace → Shared → designer-recon-accelerator → demo_01_cashflow_rec →
`README.md`**. Summary:
1. Run `generate_cashflow_rec` once → lands the workbooks + rolling file in the Volume and builds
   the tables. (In the room you can **drag a bank-rec `.xlsx` onto a Designer canvas** to show it
   ingesting Excel directly.)
2. **+ New → Data prep** → blank canvas.
3. **Add source** → `cf_prior_rec` (rolling file) and `cf_period_extract` (this period parsed).
4. **Join** on `account_code` (left) — name **append this period**.
5. **SQL / select** → rename `current_period` → `Jul_Current`, `period_control` → `Jul_Control`,
   keep the prior columns. You're adding two *named* columns — no positional maths.
6. **Output** → table `cf_cashflow_rec_designer` → **Run**.
7. **One-prompt alternative:** the **✨ Generate** prompt in the folder README.
8. **Prove it:** open **demo_01_cashflow_rec → `02_parse_append_parity.py`**, **Run all** →
   **✅ PARITY to the penny** vs `cf_benchmark`, and the **formatted Excel** lands in
   `recon_landing/uc1/output/`.
9. **See & amend code / govern / co-edit:** **</> Code** toggle; Catalog Explorer →
   `cf_cashflow_rec` → **Lineage**; **Schedule**; **Share** as **Can Edit**.

### UC2 · Control sheet — Lakeflow Designer
Full click-through: **demo_02_control_sheet → `README.md`**. Summary:
1. **+ New → Data prep** → blank canvas.
2. **Add source** → `cs_payments`, `cs_category_lookup`.
3. **Join** on `supplier` — name **lookup category** (the VLOOKUP).
4. **SQL** to derive the branch key; **Aggregate** group by `branch` sum `amount_paid` →
   `branch_total`; **SQL** to add the `MAIN (all payments)` total + `variance` (exact SQL in the
   folder README). These are the ~6–7 category tables and the summary that sums them.
5. **Output** → table `cs_control_sheet` → **Run**.
6. **One-prompt alternative** and the code/govern/co-edit beats — folder README.
7. **Prove it:** **demo_02_control_sheet → `02_parity.py`**, **Run all** → **✅ PARITY**: branches
   match the coded control sheet and tie back to the main total with **0.00 variance**.

### UC3 · Scheduled automation — Jobs + Autoloader + audit
Full detail: **demo_03_automation → `README.md`**.
1. **File staging (3a):** open **`01_file_staging.py`**, **Run all** (or job
   `automation_file_staging`). Lands versioned files in two folders under `recon_landing/uc3a/`,
   Autoloader → `af_files_bronze`, selects the **highest version per folder + report code by
   name** → `af_files_staged`, **copies** them to `uc3a/destination/`, appends to
   `af_staging_audit`. Then **Schedule** it.
2. **Fixed-width parser (3b):** open **`02_fixedwidth_parser.py`**, **Run all** (or job
   `automation_bdx_parser`). Writes ~30 daily fixed-width files (two seeded to *not* tie), parses
   by position, consolidates → `fw_bdx_consolidated`, runs the **per-file contra check** →
   `fw_contra_log`, writes the consolidated CSV + a `run_summary_*.txt`.
3. **The point:** show the **Job run history** + the run-log tables + Catalog **Lineage** — the
   scheduled, autonomous, audited automation the desktop tool can't give, with files that flow
   the moment they land.

---

## 7. The lines to land
1. *You never write or read code on UC1/UC2 — and every figure is reconciled to the penny, so
   you never take the AI on faith either.*
2. *The positional hack that made the cash-flow rec "disgusting" simply doesn't exist here — you
   append two named columns, and the formatted Excel comes out automatically.*
3. *Designer does the visual reconciliation (UC1, UC2). The scheduling, autonomous runs and audit
   trail (UC3) come from the platform — and no one moves a file by hand.*

---

## 8. Troubleshooting
| Symptom | Fix |
|---|---|
| Designer picker shows no tables | Point its catalog/schema at **lr_dev_aws_us_catalog / designer_recon_demo**. |
| Can't drag an `.xlsx` onto the canvas | Enable Excel file-format support in workspace settings (default-on since Jul 2026). |
| `02_parity` says "canvas output pending" | Build the canvas first; set its Output table (UC2 `cs_control_sheet`). |
| `DELTA_METADATA_MISMATCH` on an audit/log table | A stale table from an earlier schema — `DROP TABLE` it once; the notebooks recreate it. |
| Tables missing | Run the `[recon-accel]` generator/automation jobs — §5. |
| A notebook can't find Data prep | Lakeflow Designer isn't enabled in that workspace; UC1/UC2 live build needs it (UC3 still runs). |

---

## 9. Running in a customer sandbox
`git clone`, edit `databricks.yml` targets, `databricks bundle deploy`, run the jobs, set each
notebook's `catalog_name` / `schema_name` widgets. All data is synthetic and generated in-place —
nothing customer-specific ever leaves.
