# Use Case 3 — Scheduled automation (the Python jobs) + the audit trail

Two small automations that today run as Python scripts a licensed user kicks off by hand:
1. **File staging** — scan folders, pick the earliest version of each report for a period,
   stage it (`01_file_staging.py`).
2. **Fixed-width parsing + contra reconciliation** — parse a fixed-width payment export by
   column position, net the contra reversals, consolidate and validate (`02_fixedwidth_parser.py`).

**The honest framing (and the answer to the team's explicit question):** these are *not*
Lakeflow Designer flows — they're file/OS logic and positional parsing, not visual
transforms. On Databricks they belong in a **Lakeflow Job** (a Python/notebook task), and the
platform gives you exactly what the question asked for:

- **Scheduled, autonomous execution** — a Lakeflow Job runs "on the 1st of each month, process
  last month" with no licensed user in the loop; **Autoloader** ingests only new files.
- **Audit & logging for compliance** — every run is in the **Job run history**; this demo also
  writes an `af_staging_audit` run-log table; and Unity Catalog's `system.access.audit` +
  table **lineage/versioning** give an end-to-end, tamper-evident trail.

So: *Designer is the visual-transform layer (UC1, UC2); scheduling, autonomous runs and
audit come from the platform — comprehensively — just not from Designer itself.*

## Run it
- `01_file_staging.py` (or job `automation_file_staging`) → lands versioned report files in
  the `recon_landing` volume, Autoloader ingests them (`af_files_bronze`), stages the earliest
  per report code (`af_files_staged`), and appends a row to `af_staging_audit`.
- `02_fixedwidth_parser.py` (or job `automation_bdx_parser`) → writes a synthetic fixed-width
  file to the volume, parses it by position, negates contra rows, and writes
  `fw_bdx_consolidated` with `gross_total` vs contra-adjusted `reconciled_total`.

Then **Schedule** either notebook as a Lakeflow Job (Workflows → the job → **Schedule**).

## About this demo
All data is synthetic — report codes, files, banks, payers and payees are invented. No real
system or payment. The scripts demonstrate a pattern, not a firm's production controls.
