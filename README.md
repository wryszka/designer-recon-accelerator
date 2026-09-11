# Designer Recon Accelerator

**Finance & audit reconciliation, off the desktop ETL tool and onto a governed platform** —
built around **Lakeflow Designer**, with the scheduling and audit trail the desktop tool can't
give you.

Three workflows a finance/audit team runs today in a desktop ETL tool (Alteryx, Power Query,
KNIME) plus Python:

| Chapter | Use case | Built with |
|---|---|---|
| `demo_01_cashflow_rec` | **Cash-flow rec** — read header cells from ~20 bank-rec workbooks, append two new columns (Current + Control) onto a rolling file; missing → fallback; **formatted Excel** out | Lakeflow Designer + parity |
| `demo_02_control_sheet` | **Control sheet** — split payments into ~6–7 category tables; a summary sheet sums them and ties back to the whole with **0.00 variance** | Lakeflow Designer + parity |
| `demo_03_automation` | **Scheduled automation** — 3a pick the right file version by name + copy; 3b parse ~30 fixed-width files, contra-check each, consolidate + log | Lakeflow Jobs + Autoloader + UC audit |

UC1 & UC2 each ship a drag-and-drop build **and** a one-AI-prompt build, a parity check
(reconciled to the penny), and the code-view / amend / govern / co-edit beats. UC3 is the
honest answer to *"can the platform schedule and log like our scripts?"* — yes, via Jobs +
Autoloader + Unity Catalog audit.

## Quick start
```bash
git clone https://github.com/wryszka/designer-recon-accelerator.git
cd designer-recon-accelerator
databricks bundle deploy -t dev
databricks bundle run generate_cashflow_rec   -t dev
databricks bundle run uc1_parse_append_parity -t dev
databricks bundle run generate_control_sheet  -t dev
databricks bundle run automation_file_staging -t dev
databricks bundle run automation_bdx_parser   -t dev
```
Then follow [`docs/RUNBOOK.md`](docs/RUNBOOK.md). Portable to any workspace/sandbox via the
`catalog_name` / `schema_name` widgets.

## Design principles
- **One schema, prefixed tables** (`cf_` cash-flow rec, `cs_` control sheet, `af_`/`fw_` automation).
- **Synthetic only** — no customer names or data anywhere; desktop ETL referenced as a workflow
  *shape*, not a product comparison.
- **Parity everywhere** — the migrated result is proven equal to a coded benchmark (UC1/UC2).
- **Serverless & scale-to-zero.**

## About this demo
All data is synthetic and fabricated. This is a demonstration of Databricks capabilities on a
representative reconciliation estate; it does not represent any real organisation's data.
