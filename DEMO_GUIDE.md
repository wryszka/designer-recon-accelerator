# Designer Recon Accelerator — Demo Guide

One repo, one story: **the reconciliation work a finance/audit team does in a desktop ETL
tool, done visually on a governed platform** — plus the scheduling and audit the desktop tool
can't give. The full, click-by-click presenter guide is [`docs/RUNBOOK.md`](docs/RUNBOOK.md);
the anonymised source use cases are in [`docs/USE_CASES.md`](docs/USE_CASES.md).

## Chapters
| # | Use case | Folder | Built with |
|---|---|---|---|
| 1 | **Cash-flow rec** (append two period columns to a rolling file; formatted Excel out) | `demo_01_cashflow_rec/` | Lakeflow Designer + parity |
| 2 | **Control sheet** (~6–7 category tables summed back to the whole, 0.00 variance) | `demo_02_control_sheet/` | Lakeflow Designer + parity |
| 3 | **Scheduled automation** (3a version-by-name staging; 3b fixed-width + per-file contra) | `demo_03_automation/` | Lakeflow Jobs + Autoloader + UC audit |

## Shared conventions
- **One schema** `designer_recon_demo`; tables prefixed by use case (`cf_`, `cs_`, `af_`/`fw_`).
- **Deploys to** `/Workspace/Shared/designer-recon-accelerator/`; portable via `catalog_name` /
  `schema_name` widgets.
- **Parity everywhere** (UC1/UC2) — the canvas is proven equal to a coded benchmark to the penny.
- **Synthetic data throughout**; no customer names anywhere.

## Each Designer chapter (UC1, UC2) ships
- a **drag-and-drop** build and a **one-AI-prompt** build,
- a **parity** notebook (UC1 `02_parse_append_parity.py`, UC2 `02_parity.py`) — reconcile, don't trust the SQL,
- the **see & amend the code** (non-coder → engineer hand-off), **govern** (version/lineage/
  schedule) and **co-edit** (Share → Can Edit) beats.

## Pre-flight & run of show → [`docs/RUNBOOK.md`](docs/RUNBOOK.md)
