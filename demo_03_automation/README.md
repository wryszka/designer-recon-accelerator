# Use Case 3 — Scheduled automation (the Python jobs) + the audit trail

Two automations that today run as Python scripts a licensed user kicks off by hand — and that
are really about **moving and consolidating files**, not transforming data:

1. **3a · File staging** (`01_file_staging.py`) — files land in **two folders** on a schedule;
   pick, for each report code, the **correct version by file name** (not the latest-arrived —
   a v02 that came on the 28th still beats a v01 from the 29th), and **copy** the chosen files to
   a destination folder. Nothing inside the files changes.
2. **3b · Fixed-width BDX** (`02_fixedwidth_parser.py`) — each day a **fixed-width** file lands;
   monthly, run through all ~30 of last month's files, **parse by position**, tag every row with
   its source file, run a **contra check per file** (the detail rows must sum to that file's
   contra row), **consolidate** everything into one output, and emit a **run log / summary**.

**The honest framing (and the answer to the team's explicit question):** these are *not* Lakeflow
Designer flows — they're file/OS logic and positional parsing. On Databricks they belong in a
**Lakeflow Job** (a Python/notebook task), and the platform gives exactly what was asked for:

- **Scheduled, autonomous execution** — a Job runs "on the 1st, process last month" with no
  licensed user in the loop; **Autoloader** fires the moment files land, so no one moves files.
- **Audit & logging for compliance** — every run is in the **Job run history**; this demo also
  writes `af_staging_audit` (3a) and `fw_contra_log` + a `run_summary_*.txt` (3b); and Unity
  Catalog's `system.access.audit` + table lineage/versioning give an end-to-end trail.

So: *Designer is the visual-transform layer (UC1, UC2); scheduling, autonomous runs and audit
come from the platform — comprehensively — just not from Designer itself.*

## Where everything is

Volume `recon_landing` (Catalog → `lr_dev_aws_us_catalog` → `designer_recon_demo` → Volumes):
- `uc3a/sources/folder_a/`, `uc3a/sources/folder_b/` — versioned incoming files
- `uc3a/destination/` — the chosen versions, copied here
- `uc3b/incoming/` — the ~30 daily fixed-width files
- `uc3b/output/consolidated_<period>/` (CSV) + `uc3b/output/run_summary_<period>.txt`

Tables (schema `designer_recon_demo`):

| Table | Use case | What it holds |
|---|---|---|
| `af_files_bronze` | 3a | every file Autoloader has seen |
| `af_files_staged` | 3a | the selected highest version per folder + report code |
| `af_staging_audit` | 3a | one row per run (files seen / staged / copied) |
| `fw_bdx_consolidated` | 3b | all files' detail rows, tagged with `source_file` |
| `fw_contra_log` | 3b | per-file contra check: detail sum vs contra row, MATCH / MISMATCH |

## Run it
- `01_file_staging.py` (or job `automation_file_staging`) → lands versioned files in two folders,
  Autoloader → `af_files_bronze`, selects the highest version per folder+code by name →
  `af_files_staged`, copies them to `uc3a/destination/`, appends to `af_staging_audit`.
- `02_fixedwidth_parser.py` (or job `automation_bdx_parser`) → writes ~30 daily fixed-width files
  (two seeded to *not* tie), parses by position, consolidates the detail rows → `fw_bdx_consolidated`,
  runs the per-file contra check → `fw_contra_log`, and writes the consolidated CSV + summary.

Then **Schedule** either notebook as a Lakeflow Job (Workflows → the job → **Schedule**).

## The beats to land
- **No one moves files** — drop them and Autoloader fires; the right version is chosen by name,
  the fixed-width files are parsed and consolidated, all unattended.
- **It catches what it should** — the contra log flags the two files that don't tie to their
  contra row, with the exact difference.
- **Fully audited** — Job run history + the run-log tables + Unity Catalog lineage.

## About this demo
All data is synthetic — report codes, files, banks, payers and payees are invented. No real
system or payment. The scripts demonstrate a pattern, not a firm's production controls.
