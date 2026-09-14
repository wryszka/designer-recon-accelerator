# Working Session — Our Proposed Plan

A **one-hour working session** built around the Designer use cases you shared — with **Excel at
both ends**, because that's how your team works. We'll take the reconciliation and control-sheet
work you do today in a desktop ETL tool and Python, and show it rebuilt **no-code on Lakeflow
Designer**: Excel in, Excel out, and **nobody moving files by hand**.

*All examples use synthetic data that mirrors the shape of your workflows — no real figures.*

---

## The through-line

**Excel in → Designer in the middle → Excel out.** Your files start and end as Excel because
that's what your teams and auditors need; Designer is just the governed engine in between, and the
moment a file lands the work runs — no one drags it from folder to folder.

---

## What we'll show

**1 · Your cash-flow rec, on Designer — Excel in, Excel out** *(the main event)*
The monthly rec you run across ~20 bank accounts. The bank-rec **Excel** workbooks and last
month's rolling **Excel** file go in; Designer reads them and **appends this period's two columns**
(Current + Control) with no code — the very thing that forced the five-input positional workaround
in the desktop tool — and a **formatted Excel** comes out the other end **automatically**. No
template, no Format Painter. If an account's workbook is missing, the fallback path handles it.

**2 · Trust it, and change it**
Build a step by **drag-and-drop** or by typing **one plain-English instruction**. Then **open the
code underneath** — it's real, versioned SQL. A more technical colleague can tighten it directly
and the change **reflects straight back into the visual canvas**. **Co-edit** it live, with
automatic **lineage**, **version history** and one-click **scheduling**.

**3 · Your control sheet, on Designer**
Join the category lookup onto your data, split it into the **six or seven tables** you produce, and
a **summary control sheet** sums them and **ties back to the whole with 0.00 variance** — proven to
the penny, Excel in and out.

**4 · Stop moving files** *(a quick look)*
Your file-staging and fixed-width jobs, running the moment files land (**Autoloader**) — the right
version picked automatically, the contra checks run, everything consolidated, scheduled and audited.
No licensed user in the loop, no manual file-shuffling.

**And beyond the hour:** the same governed data answers plain-English questions (**Genie**), drives
a live **dashboard**, and supports **forecasting** — the natural next session.

---

## Your challenges → how we'll tackle them

| What you told us | How we'll address it | Built with |
|---|---|---|
| The cash-flow rec (read cells from many workbooks, append columns, formatted Excel out) | Rebuilt no-code, Excel in and out, columns appended by name — the positional workaround disappears | **Lakeflow Designer** |
| "Is it accessible for non-coders?" | Drag-and-drop *or* one plain-English instruction — no SQL to write | **Designer** |
| "Can we trust it, and see / change the logic?" | Real versioned code underneath — view it, amend it, and prove the result **to the penny** | **Designer** + parity |
| "Can a colleague QA or co-own it?" | Hand the flow over or co-edit it live; every change versioned | **Designer** |
| The control sheet (split into tables, summarise, tie back) | Split into your 6–7 tables + a summary that sums each to 0.00 variance | **Designer** |
| "Can it schedule and log like our scripts, and stop the file-shuffling?" | Jobs + Autoloader fire on arrival, with a full audit trail | **Jobs + Autoloader** |
| Everything wants to be Excel | Excel in (workbooks, rolling file) and formatted Excel out — automatically | **Designer + Jobs** |

---

## To make it yours

Everything is synthetic today. When you're ready, we shape the examples to your real column
layouts and connect to your sources directly, so the same flows run on your live data in your
own governed space.

*All demonstration data is synthetic and does not represent any real figures. Desktop ETL tools
are referenced as a way of working, not as a product comparison.*
