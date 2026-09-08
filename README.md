# Designer Recon Accelerator

**Finance & audit reconciliation, off the desktop ETL tool and onto a governed platform** —
built around **Lakeflow Designer**, with the scheduling and audit trail the desktop tool can't
give you.

Three workflows a finance/audit team runs today in a desktop ETL tool (Alteryx, Power Query,
KNIME) plus Python:

| Chapter | Use case | Built with |
|---|---|---|
| `demo_01_cash_matching` | **Cash matching** — reconcile 40+ bank accounts (ledger vs bank + timing items); each nets to zero, exceptions flagged | Lakeflow Designer + parity |
| `demo_02_control_sheet` | **Control sheet** — split payments into branches that tie back to the main total with **0.00 variance** | Lakeflow Designer + parity |
| `demo_03_automation` | **Scheduled automation** — file staging + fixed-width parsing/contra | Lakeflow Jobs + Autoloader + UC audit |

UC1 & UC2 each ship a drag-and-drop build **and** a one-AI-prompt build, a parity check
(reconciled to the penny), and the code-view / amend / govern / co-edit beats. UC3 is the
honest answer to *"can the platform schedule and log like our scripts?"* — yes, via Jobs +
Autoloader + Unity Catalog audit.

## Quick start
```bash
git clone https://github.com/wryszka/designer-recon-accelerator.git
cd designer-recon-accelerator
databricks bundle deploy -t dev
databricks bundle run generate_cash_matching -t dev
databricks bundle run generate_control_sheet -t dev
databricks bundle run automation_file_staging -t dev
databricks bundle run automation_bdx_parser -t dev
```
Then follow [`docs/RUNBOOK.md`](docs/RUNBOOK.md). Portable to any workspace/sandbox via the
`catalog_name` / `schema_name` widgets.

## Design principles
- **One schema, prefixed tables** (`cm_` cash matching, `cs_` control sheet, `af_`/`fw_` automation).
- **Synthetic only** — no customer names or data anywhere; desktop ETL referenced as a workflow
  *shape*, not a product comparison.
- **Parity everywhere** — the migrated result is proven equal to a coded benchmark (UC1/UC2).
- **Serverless & scale-to-zero.**

## About this demo
All data is synthetic and fabricated. This is a demonstration of Databricks capabilities on a
representative reconciliation estate; it does not represent any real organisation's data.
