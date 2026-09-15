# Auto Loader mini-demo — folder → table

The simplest possible "**drop a file in a folder, it lands in a table**" story. You keep the habit
you have today (put a file in a folder); the platform picks it up and **appends** it — no code, no
one moving files around.

## The whole flow (4 lines of SQL — `pipeline.sql`)
```sql
CREATE OR REFRESH STREAMING TABLE al_landing_demo AS
SELECT *, _metadata.file_name AS source_file
FROM STREAM read_files(
  '/Volumes/lr_dev_aws_us_catalog/designer_recon_demo/recon_landing/autoloader_demo/landing',
  format => 'excel', headerRows => 1, schemaEvolutionMode => 'none');
```
That's it. `STREAM read_files(...)` **is** Auto Loader — it remembers which files it has already read,
so each run only picks up the new ones. Runs as a serverless **Lakeflow pipeline** (`autoloader_demo`).

## Where everything is
| Thing | Location |
|---|---|
| Folder Auto Loader watches | `…/recon_landing/autoloader_demo/landing/` (Excel only) |
| **File that sits there** (ingested first) | `landing/movements_2026-07-01.xlsx` |
| **File you drop live** | `to_drop/movements_2026-07-02.xlsx` — drag it into `landing/` |
| The table | `lr_dev_aws_us_catalog.designer_recon_demo.al_landing_demo` |
| CSV versions (if you'd rather show csv) | `…/autoloader_demo/csv_versions/` |

## Demo steps (razor-sharp)
1. **Setup (once):** run job `make_autoloader_files` — puts file 1 in `landing/`, file 2 in `to_drop/`.
2. **First run:** run pipeline **`autoloader_demo`** → open `al_landing_demo`: **3 rows** (file 1), each
   tagged with its `source_file`.
3. **The moment:** drag **`movements_2026-07-02.xlsx`** from `to_drop/` into `landing/`.
4. **Run the pipeline again** → `al_landing_demo` now has **6 rows** — file 2 **appended**, no code, no
   re-keying. *"You dropped a file; it's in the table. That's the whole thing."*

## Build it with a prompt (Genie / Databricks Assistant)
Paste this — it generates the flow above:
> *In lr_dev_aws_us_catalog.designer_recon_demo, create a streaming table called al_landing_demo that
> uses Auto Loader to ingest every Excel file in the volume folder
> /Volumes/lr_dev_aws_us_catalog/designer_recon_demo/recon_landing/autoloader_demo/landing. Read the
> first row as the header, don't evolve the schema, and add a column source_file with the file name.
> When a new Excel file is dropped in the folder, its rows should be appended automatically.*

## Notes
- **Can Designer do this?** Designer can point at a folder and union the files, but it re-reads them all
  each run — it's not the incremental "new file appends" behaviour. For that, use this streaming table
  (Auto Loader). Keep Designer for the *transforms* (UC1/UC2).
- **CSV instead of Excel:** point `read_files` at the `csv_versions/` folder and use `format => 'csv'`
  (drop the Excel-only options). Everything else is identical.
- Excel ingestion needs DBR 17.1+ (serverless pipelines are current); keep the landing folder
  **Excel-only** — a stray `.csv` there makes the Excel reader choke.
