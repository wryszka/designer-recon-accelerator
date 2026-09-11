# UC1 · Cash-flow rec (Lakeflow Designer)

The monthly cash-flow reconciliation: pull a few summary cells off each account's bank-rec
workbook and **append two new columns** (this period's *Current* and *Control*) onto a single
**rolling file** that carries one column-pair per period across the financial year. If an
account's workbook is missing, a **fallback** pulls two cells from separate SAP and Bank folders.

This is the process that forced the "disgusting" 5-input positional hack in the desktop ETL tool
(no variables → the new column's position moves every month). On Databricks you append two
*named* columns — the problem doesn't exist — and the formatted Excel comes out automatically.

## What the notebooks build

| Notebook | What it does |
|---|---|
| `01_generate_sources.py` | writes the synthetic inputs into the `recon_landing` Volume and the baseline tables |
| `02_parse_append_parity.py` | reads the header cells, appends the two columns, proves parity to the penny, writes the formatted Excel |

Run `generate_cashflow_rec` once, then `uc1_parse_append_parity` (both defined in `databricks.yml`).

## Where everything is (crystal clear)

**Input files** — UC Volume `recon_landing`, under
`/Volumes/<catalog>/designer_recon_demo/recon_landing/uc1/`:
- `bank_recs/BankRec_ACC-0xx_2026-07.xlsx` — one per account; `Header` sheet holds **SAP / Accurate / Bank / Control**
- `sap_fallback/`, `bank_fallback/` — 2-cell fallback for the 3 accounts with no workbook
- `prior/CashFlowRec_2026-06.xlsx` — last month's rolling file
- `output/CashFlowRec_2026-07.xlsx` — the formatted output the job produces

**Tables** — schema `designer_recon_demo`:
- `cf_accounts` — account reference
- `cf_prior_rec` — the rolling file as a (wide) table = the running baseline
- `cf_period_extract` — this period parsed from the files: Current + Control per account (+ `source`)
- `cf_cashflow_rec` — the produced output (prior + the two new columns)
- `cf_benchmark` — the expected output; `02` proves the canvas/coded result matches it to the penny

## Build it in Lakeflow Designer (the workshop path)

Goal: reproduce `cf_cashflow_rec` visually and prove it equals `cf_benchmark`.

**Drag-and-drop**
1. **Source** → `cf_prior_rec` (the rolling file).
2. **Source** → `cf_period_extract` (this period's parsed Current/Control).
3. **Join** the two on `account_code` (left join — keep every account).
4. **SQL / select** → rename `current_period` → `Jul_Current`, `period_control` → `Jul_Control`;
   keep the prior period columns as-is (you're just adding two named columns — no positional maths).
5. **Output** → a table (e.g. `cf_cashflow_rec_designer`).

**Or one AI prompt** (✨ *Generate*): *"Join the rolling cash-flow file to this period's extract on
account_code, add the extract's current and control values as two new columns named Jul_Current
and Jul_Control, and keep all existing period columns."*

**Reading the raw Excel:** the header-cell extraction (SAP/Accurate/Bank/Control → Current/Control)
is done in `01`/`02` because it lifts *specific cells*, not a tabular read. In the workshop you can
still **drag a `.xlsx` onto the canvas** to show Designer ingesting Excel directly (it lands in a
Volume and creates a Source) — then the flow above runs on the tidy `cf_period_extract`.

## The beats that answer their questions
- **Non-coders** — the whole flow is drag-and-drop, or one plain-English prompt. No SQL to write.
- **Trust & change the logic** — open the **code pane**: the flow is real, versioned SQL. A technical
  colleague tightens it directly and the change reflects back into the canvas.
- **Work together** — **Share → Can Edit** and co-author the same flow; every change is versioned.
- **Parity** — run `02_parse_append_parity.py`: ✅ to the penny against `cf_benchmark`. You tie it out;
  you don't take the generated SQL on trust.
- **Formatted Excel** — `02` writes a styled `CashFlowRec_2026-07.xlsx` (headers, currency formats,
  control breaks in red, frozen panes). No template + Format-Painter dance.

*All data synthetic. No real organisation, bank or account.*
