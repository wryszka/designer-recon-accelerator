# Working Session — Our Proposed Plan

**Purpose of today (30 minutes):** to walk you through how we intend to use the upcoming
**90-minute working session**, and to check it against your priorities *before* we build it —
so you can tell us what's on target, what's missing, and what to put first.

The plan is built entirely around **the requirements and questions your team shared with us**:
the reconciliation and automation workflows you run today, and the analytics and forecasting
questions on your book. Everything is shown on one governed platform, using **Lakeflow Designer**
(visual, no-code data prep), **Genie** (ask your data in plain English) and **AI/BI dashboards**.

*All examples use synthetic data that mirrors the shape of your workflows — no real figures.*

---

## Your challenges → how we'll tackle them

| What you told us | How we'll address it | Built with |
|---|---|---|
| Reconciliations (cash matching, control sheet) run today in a desktop ETL tool | Rebuild them on a visual, no-code canvas — nothing on a local desktop | **Lakeflow Designer** |
| "Is it accessible for non-coders?" | Build by drag-and-drop *or* by typing one plain-English instruction — no SQL to write | **Designer** |
| "Can we trust it? Can we see and change the logic?" | Every flow is real, versioned code underneath — view it, amend it, and prove the result **to the penny** against a known-good benchmark | **Designer** + parity check |
| "Can a colleague QA or co-own it?" | Hand a flow to a technical colleague who edits the code directly (it reflects back into the canvas), or co-edit the same flow live | **Designer** (collaboration) |
| "Can it schedule and log like our current scripts?" | Your automations run as scheduled jobs, unattended, with a full audit trail and run history | **Jobs + Autoloader + governed audit** |
| Handling incoming file drops / changing columns | New files are picked up automatically and staged, with schema changes handled safely | **Autoloader** |
| Your analytics questions (quotes, conversion, renewals, lapses, book performance) | Ask them in plain English — the platform writes and runs the query and explains itself | **Genie** |
| Ongoing monitoring of the book | A live, governed dashboard on the same data | **AI/BI dashboard** |
| Forecasting (volumes, renewals, targets) | Built-in forecasting over the same governed tables | **AI/BI + forecasting** |

---

## The 90-minute session — what we plan to show

Roughly **60 minutes of demonstration**, leaving **~30 minutes for your questions and discussion**.

**1 · Your reconciliations, no-code (Designer)** — *~18 min*
Cash matching built live (reconcile the accounts, each nets to zero, exceptions flagged), proven
to the penny; then the control sheet, where every branch ties back to the whole with zero variance.

**2 · Trust it, and work on it together** — *~12 min*
The same flow built from a plain-English prompt; viewing and amending the underlying code;
co-editing; and the governance around it — lineage, version history, and scheduling.

**3 · Automate and audit** — *~10 min*
Your automations as scheduled jobs with automatic file pick-up and a complete audit trail —
the direct answer to whether the platform can schedule and log like your current scripts.

**4 · Ask and forecast your book** — *~15 min*
Your analytics questions answered in plain English (Genie), a live dashboard on the same data,
and forecasting for the periods ahead.

**Close & discussion** — *~30 min* — your questions, and agreeing the next workflows to tackle.

---

## What we'd like to confirm with you today

1. **Are these the right workflows?** Have we captured your cash-matching and control-sheet
   processes correctly — anything to add or change?
2. **Priorities.** Items 1–3 are your day-to-day workflows; item 4 is the wider analytics story.
   Is that the right emphasis, or would you weight it differently?
3. **Depth vs. breadth.** Would you rather we go deeper on the reconciliations, or keep all four
   items in the 90 minutes?
4. **Data.** Are synthetic examples fine for the session, or would you like them shaped to your
   real column layouts (a sample file or field list would let us do that)?
5. **Logistics.** Confirm date, attendees, and who from your side would like hands-on afterwards.

*All demonstration data is synthetic and does not represent any real figures. Desktop ETL tools
are referenced as a way of working, not as a product comparison.*

---

## Clarifying questions

To make the 90-minute session reflect how your workflows *actually* run — not just their
headline purpose — it would help to understand a few things beforehand. The more of these we
can pin down, the closer we can build to your real process.

**Cash matching**
- Is matching exact (reference + amount), or do you match with **tolerances / fuzzy** on
  references and amounts?
- Is it one-to-one, or **one-to-many / many-to-one** (a single bank line clearing several
  ledger items)?
- Are there **suggested or partial matches** a person confirms — and how are **unmatched items**
  handled (carried forward, aged, written off)?

**Exceptions & review**
- Once an exception is flagged, what happens — who reviews it, do they **annotate / assign** it,
  and does the outcome feed back in for the next run?
- Do **open items persist across periods** (aging), or is each run standalone?

**Inputs & reference data**
- How many **sources** feed the workflow (bank feeds, ledgers, sub-ledgers, adjustments), and do
  the **formats differ** per source?
- Which **lookup / mapping tables** does it rely on (GL codes, branch/supplier maps, FX rates),
  and **who maintains** them today?

**Logic & structure**
- Does the workflow use **macros or repeated / looping steps**?
- Are there **business rules or edge cases** built up over time that aren't written down anywhere?

**Outputs & distribution**
- What comes out at the end — a table, a **formatted Excel / PDF pack**, an **email** to a
  distribution list, a posting to another system?

**Automation & controls**
- What's the current **schedule** and the **dependency chain** (wait for file → extract → run →
  distribute)?
- Are there **control gates** (e.g. don't proceed unless totals tie) or **sign-off / approval**
  steps we should reflect?

**Scale**
- Rough **volumes** (rows / files per run, how many accounts or branches), and any **month-end /
  quarter-end** differences.

**And the most useful of all —**
- Could we **see the workflow itself**? Even a screenshot of the full canvas, or an export of the
  workflow file, would let us map it precisely and make sure nothing is missed.
