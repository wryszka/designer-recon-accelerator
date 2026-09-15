# Designer Recon Accelerator — Setup & technical notes (NOT for the room)

**This document is for the person building/refreshing the demo. It is never opened during the session.**
The presenter guide is `docs/RUNBOOK.md`, which is deliberately 100% no-code. Everything technical —
notebooks, the coded receipts that prove parity, and the rebuild commands — lives here so it never leaks
onto a projector in front of a no-code audience.

Repo: https://github.com/wryszka/designer-recon-accelerator (public).
Workspace: `/Workspace/Shared/designer-recon-accelerator`. DEV catalog/schema
`lr_dev_aws_us_catalog.designer_recon_demo`; warehouse `a3b61648ea4809e3`; Volume `recon_landing`.

---

## What's code vs. what's the demo

- **The demo surface (RUNBOOK):** the Designer canvas, Excel files in the Volume, result tables opened as
  spreadsheet grids, Job run history, Genie/dashboard. **No code shown, ever.**
- **The code (this doc only):** notebooks that (a) generate the synthetic inputs, (b) ingest via Auto Loader,
  and (c) are a **coded mirror of each Designer flow that proves it ties to the penny** — our own QA. In a
  real customer deployment there is no "benchmark" to compare against; the parity notebooks are demo
  scaffolding, not something a customer runs or maintains.
- **Trust feature for their engineers (not the room):** every Designer flow exposes a **`</> Code`** pane
  showing the SQL it generated — a technical reviewer can read/export it. Mention only to an engineer who
  asks off to the side; never on screen in the main session.

## One-time rebuild — CLI, profile `DEV`
Run this before the session to populate all tables and files. It is the only place these commands appear.
```bash
git clone https://github.com/wryszka/designer-recon-accelerator.git && cd designer-recon-accelerator
databricks bundle deploy -t dev -p DEV
databricks bundle run generate_cashflow_rec     -t dev -p DEV
databricks bundle run uc1_ingest_autoloader     -t dev -p DEV   # Auto Loader → cf_period_extract
databricks bundle run uc1_parse_append_parity   -t dev -p DEV   # coded mirror + parity + Excel export
databricks bundle run generate_control_sheet    -t dev -p DEV
databricks bundle run uc2_control_sheet_parity  -t dev -p DEV
databricks bundle run automation_file_staging   -t dev -p DEV
databricks bundle run automation_bdx_parser     -t dev -p DEV
```

## Notebooks (code — engineers only, never the projector)
**UC1** (`demo_01_cashflow_rec/`):
- generate: https://github.com/wryszka/designer-recon-accelerator/blob/main/demo_01_cashflow_rec/01_generate_sources.py
- Auto Loader ingest (job `uc1_ingest_autoloader`): https://github.com/wryszka/designer-recon-accelerator/blob/main/demo_01_cashflow_rec/00_ingest_autoloader.py
- coded mirror + parity + Excel (job `uc1_parse_append_parity`): https://github.com/wryszka/designer-recon-accelerator/blob/main/demo_01_cashflow_rec/02_parse_append_parity.py

**UC2** (`demo_02_control_sheet/`):
- generate: https://github.com/wryszka/designer-recon-accelerator/blob/main/demo_02_control_sheet/01_generate_sources.py
- coded mirror + population reconciliation + Excel (job `uc2_control_sheet_parity`): https://github.com/wryszka/designer-recon-accelerator/blob/main/demo_02_control_sheet/02_parity.py

**UC3** (`demo_03_automation/`):
- 3a file staging (job `automation_file_staging`): https://github.com/wryszka/designer-recon-accelerator/blob/main/demo_03_automation/01_file_staging.py
- 3b BDX parse + contra (job `automation_bdx_parser`): https://github.com/wryszka/designer-recon-accelerator/blob/main/demo_03_automation/02_fixedwidth_parser.py

**Optional bonus (`demo_00_autoloader/`):** a 4-line streaming table that appends the moment a new Excel
lands (drop a file, re-run, row count 3 → 6). Back-pocket only, for a technical questioner — it's the
opposite of the "you still drop your file" reassurance a nervous room needs.

## Excel export gotcha (serverless)
`to_excel` / openpyxl **cannot** write directly to a `/Volumes` path (FUSE = `Errno 95, Operation not
supported`, no random-access write). Write to a local `tempfile.mkdtemp()` first, then `shutil.copy` to the
Volume. `to_csv` streams to `/Volumes` fine. No apostrophes in `COMMENT ON TABLE '...'` literals (parse error).

## Troubleshooting
| Symptom | Fix |
|---|---|
| Can't drag `.xlsx` onto the canvas | Enable Excel file-format support in workspace settings; or use the pre-loaded table. |
| Source picker empty | Point catalog/schema at **lr_dev_aws_us_catalog / designer_recon_demo**. |
| Parity job "canvas output pending" | Build the Designer flow + set its Output table first. |
| `DELTA_METADATA_MISMATCH` on a log table | Stale table — `DROP TABLE` it once; the notebook recreates it. |
| Tables missing | Run the rebuild commands above. |
