# Demo requirements — the client's "exam questions" (UC1–UC3)

Source: the finance team's spec — the call of **2026-09-09** + the *"Alteryx vs Designer"* deck.
These are the questions the demo must answer. **Reviewers** (see `docs/` note below and the review
personas) score the current demo against every line here, per persona, each round.

Legend for review passes: **✅ built & proven** · **🟡 answerable live but not shown/proven** · **⚠️ gap**.

---

## Cross-cutting — every UC must answer these
- **C1 · Accessible to non-coders** — a finance person builds/runs it without writing code.
- **C2 · Trustable, not a black box** — see the logic, change it, and prove the numbers (parity).
- **C3 · Collaborative** — a colleague can QA / co-own the *same* flow, every change versioned.
- **C4 · Scheduled, unattended & audited** — runs on a schedule with no licensed user in the loop,
  with an audit trail their auditors accept (who changed what, when, why — not just lineage).
- **C5 · Excel in / Excel out** — inputs arrive as Excel/CSV; outputs must be usable Excel.

---

## UC1 — Cash-flow reconciliation
- **U1.1** Read the header cells (**SAP / Accurate / Bank / Control**) from each account's monthly
  bank-rec workbook, across the folder of accounts.
- **U1.2** Append the two new period columns (**Current + Control**) onto the rolling file —
  **without the positional hack** Alteryx forced (no variable for the moving column).
- **U1.3** **Missing-workbook fallback:** pull **2 cells** from separate SAP + Bank folders instead of 4.
- **U1.4** **Each account reconciles** (Control nets to **zero**); **exceptions flagged**.
- **U1.5** **Roll across the financial year** — one column-pair per period, **12 months, reset each FY**,
  a new file produced each month.
- **U1.6** Output a **formatted Excel** automatically (kill the template + Format-Painter step).
- Plus **C1–C5**.

---

## UC2 — Control sheet
- **U2.1** **Look up a category** onto the data sheet (VLOOKUP-style join).
- **U2.2** **Split into ~6–7 separate tables** by combinations of category + other fields.
- **U2.3** A **summary control sheet** that **sums the total of each** of those tables.
- **U2.4** The **parts tie back to the whole** (0.00 variance) — that reconciliation *is* the control.
- Plus **C1–C5**.

---

## UC3 — Scheduled automation (two Python scripts; **NOT Designer** — that's the point)
Overarching question: *"can the platform schedule and log this like our scripts?"* (Answer: yes —
Lakeflow Jobs + Auto Loader + Unity Catalog audit.)

### 3a — ACS Station Journal (file staging)
- **U3a.1** From **two folders**, select — per report code — the **correct version by file name**
  (**not** latest-arrived: a v02 from the 28th beats a v01 from the 29th).
- **U3a.2** **Copy** the selected files to a destination folder (**no data change**).
- **U3a.3** Runs **automatically** on schedule / on arrival — no manual macro run, no desktop dependency.

### 3b — Avantia BDX (fixed-width + contra)
- **U3b.1** **Parse ~30 daily fixed-width files by column position** (not text-to-columns).
- **U3b.2** Tag each row with its **source file**.
- **U3b.3** **Per-file contra check:** the detail rows must **sum to that file's contra row**.
- **U3b.4** **Consolidate** all files into one output (CSV is fine here).
- **U3b.5** A **run log / summary** — which files processed + contra pass/fail (a summary email).
- **U3b.6** Scheduled, unattended, audited.

---

*How to use this:* each review round, walk the current demo against every line above from each of the
review personas, mark ✅/🟡/⚠️, and fold the fixes back into the build + runbook. Keep this file the
single source of truth for "what the client actually asked for."
