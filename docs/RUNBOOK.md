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
Three reconciliation / automation workflows that finance & audit teams run today in a desktop
ETL tool plus Python, rebuilt on Databricks:

- **UC1 — Cash matching:** reconcile 40+ bank accounts (ledger vs bank + timing items); each
  nets to zero, exceptions flagged. **Lakeflow Designer.**
- **UC2 — Control sheet:** split payments into branches; every branch ties back to the main
  total with **0.00 variance**. **Lakeflow Designer.**
- **UC3 — Scheduled automation:** file staging + fixed-width parsing/contra — **Lakeflow Jobs
  + Autoloader + Unity Catalog audit** (not Designer, and that's the honest answer to "can the
  platform schedule + log like our scripts?").

**The story:** *UC1 and UC2 are the desktop-ETL work — join, clean, aggregate, reconcile —
done visually on a governed platform and reconciled to the penny. UC3 is the scheduling and
audit trail the desktop tool can't give you. And on the Designer flows you never have to read
the SQL, nor trust it blindly — you tie it out.*

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
| Landing volume (UC3 files) | Volume `recon_landing` |
| Jobs | Workflows → jobs prefixed `[recon-accel]` |
| Public repo | `https://github.com/wryszka/designer-recon-accelerator` |

**Tables** (all in `lr_dev_aws_us_catalog.designer_recon_demo`):

| Table | Use case | What it holds |
|---|---|---|
| `cm_accounts`, `cm_gl_balances`, `cm_bank_balances`, `cm_prior_recon` | UC1 | sources |
| `cm_benchmark` | UC1 | coded reconciliation (parity oracle) |
| `cm_reconciliation` | UC1 | the table you build on the Designer canvas |
| `cs_payments`, `cs_category_lookup` | UC2 | sources |
| `cs_benchmark` | UC2 | coded control sheet (parity oracle) |
| `cs_control_sheet` | UC2 | the table you build on the Designer canvas |
| `af_files_bronze`, `af_files_staged`, `af_staging_audit` | UC3 | file-staging + audit log |
| `fw_bdx_consolidated` | UC3 | parsed fixed-width payments + contra-adjusted amounts |

---

## 3. Prerequisites
- DEV workspace access with `lr_dev_aws_us_catalog` visible; a serverless **SQL warehouse**.
- **Lakeflow Designer (GA)** — confirm via **+ New → Data prep**. Needed for UC1 & UC2's live build.
- To (re)deploy elsewhere: the **Databricks CLI**, authenticated.

---

## 4. Pre-flight — the day before
1. **Confirm the data.** Catalog → `designer_recon_demo` → check `cm_benchmark` and
   `cs_benchmark` exist. If the schema is empty, run the generators — §5.
2. **Open the surfaces once** so first load is instant: a blank **Data prep** canvas.
3. **Dry-run both Designer builds once** (UC1 §6, UC2 §6) — the canvas is live clicks, no "Run all".

---

## 5. Setup — it's built; here's how to (re)build it
On DEV (rebuild in place), CLI authenticated to profile `DEV`:
```bash
git clone https://github.com/wryszka/designer-recon-accelerator.git
cd designer-recon-accelerator
databricks bundle deploy -t dev -p DEV
databricks bundle run generate_cash_matching  -t dev -p DEV   # cm_* tables
databricks bundle run generate_control_sheet   -t dev -p DEV   # cs_* tables
databricks bundle run automation_file_staging  -t dev -p DEV   # af_* tables (UC3a)
databricks bundle run automation_bdx_parser     -t dev -p DEV   # fw_* table  (UC3b)
```
**Different workspace / sandbox:** edit `databricks.yml` targets + `catalog_name`/`schema_name`;
every notebook also has those widgets at the top. Nothing else changes.

---

## 6. Chapter-by-chapter — the verbose steps

### UC1 · Cash matching — Lakeflow Designer
Full click-through: **Workspace → Shared → designer-recon-accelerator → demo_01_cash_matching →
`README.md`**. Summary:
1. **+ New → Data prep** → blank canvas.
2. **Add source** → `cm_gl_balances`, `cm_bank_balances` (and `cm_accounts` for names). If the
   picker is empty, point its catalog/schema at **lr_dev_aws_us_catalog / designer_recon_demo**.
3. **Join** `cm_gl_balances` + `cm_bank_balances`, inner join on `account_code` — name **match gl to bank**.
4. **SQL** operator computing `variance` and a `Reconciled`/`Exception` `status` (exact SQL in
   the folder README) — name **reconcile**.
5. **Output** → table `cm_reconciliation` → **Run**. Preview: most `variance` ≈ 0; a few `Exception`.
6. **One-prompt alternative:** paste the prompt in the folder README's *"build it with ONE AI
   prompt"* section into the canvas **✨ Generate** box — Designer builds the whole flow.
7. **Prove it:** open **demo_01_cash_matching → `02_parity.py`**, **Connect** to serverless,
   **Run all** → **✅ PARITY** (all accounts match the coded reconciliation, incl. the 3 exceptions).
8. **See & amend code / govern / co-edit:** **</> Code** toggle (hand to an engineer — edits
   reflect back to the canvas); Catalog Explorer → `cm_reconciliation` → **Lineage**;
   **Schedule**; **Share** as **Can Edit** to co-own the flow.

### UC2 · Control sheet — Lakeflow Designer
Full click-through: **demo_02_control_sheet → `README.md`**. Summary:
1. **+ New → Data prep** → blank canvas.
2. **Add source** → `cs_payments`, `cs_category_lookup`.
3. **Join** on `supplier` — name **lookup category** (the VLOOKUP).
4. **SQL** operator to derive the `branch` key; **Aggregate** group by `branch` sum
   `amount_paid` → `branch_total`; **SQL** to add the `MAIN (all payments)` total + `variance`
   (exact SQL in the folder README).
5. **Output** → table `cs_control_sheet` → **Run**.
6. **One-prompt alternative** and the code/govern/co-edit beats — folder README.
7. **Prove it:** **demo_02_control_sheet → `02_parity.py`**, **Run all** → **✅ PARITY**: branches
   match the coded control sheet and tie back to the main total with **0.00 variance**.

### UC3 · Scheduled automation — Jobs + Autoloader + audit
Full detail: **demo_03_automation → `README.md`**.
1. **File staging:** open **demo_03_automation → `01_file_staging.py`**, **Connect** to
   serverless, **Run all** (or job `automation_file_staging`). Lands versioned files in Volume
   `recon_landing → reports_incoming/`, Autoloader → `af_files_bronze`, stages the **earliest**
   per code → `af_files_staged`, appends to `af_staging_audit`. Then **Schedule** it (Workflows).
2. **Fixed-width parser:** open **`02_fixedwidth_parser.py`**, **Run all** (or job
   `automation_bdx_parser`). Writes a synthetic fixed-width file, parses by position, negates
   contra rows → `fw_bdx_consolidated`; show `gross_total` vs contra-adjusted `reconciled_total`.
3. **The point:** show the **Job run history** + `af_staging_audit` + Catalog **Lineage** — the
   scheduled, autonomous, audited automation the desktop tool can't give.

---

## 7. The lines to land
1. *You never write or read code on UC1/UC2 — and every figure is reconciled to the penny, so
   you never take the AI on faith either.*
2. *Designer does the visual reconciliation (UC1, UC2). The scheduling, autonomous runs and
   audit trail (UC3) come from the platform — the part a desktop ETL tool can't do.*

---

## 8. Troubleshooting
| Symptom | Fix |
|---|---|
| Designer picker shows no tables | Point its catalog/schema at **lr_dev_aws_us_catalog / designer_recon_demo**. |
| `02_parity` says "canvas output pending" | Build the canvas first; set its Output to `cm_reconciliation` (UC1) / `cs_control_sheet` (UC2). |
| Tables missing | Run the four `[recon-accel]` generator/automation jobs — §5. |
| A notebook can't find Data prep | Lakeflow Designer isn't enabled in that workspace; UC1/UC2 live build needs it (UC3 still runs). |

---

## 9. Running in a customer sandbox
`git clone`, edit `databricks.yml` targets, `databricks bundle deploy`, run the four jobs, set
each notebook's `catalog_name` / `schema_name` widgets. All data is synthetic and generated
in-place — nothing customer-specific ever leaves.
