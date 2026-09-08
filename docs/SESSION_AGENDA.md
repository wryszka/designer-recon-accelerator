# Finance Enablement — Session Agenda & Run of Show

A working session built around **your team's own requirements**: the reconciliation and
automation workflows you shared (cash matching, control sheet, the Python automations) plus
the analytics and forecasting questions from earlier. The point is simple — *the work you do
today in a desktop ETL tool and Python, shown on one governed platform, against your examples.*

All demo data is synthetic; your workflows are reproduced as generic, anonymised examples.

---

## Logistics

- **Tomorrow — 30 minutes:** scope confirmation. Walk this agenda, agree what's in/out, confirm
  which of your examples we build against, and lock the date. *(No live build tomorrow — it's
  alignment.)*
- **Main session — moved to next week, ~90 minutes:** we'll plan the demo to **~60 minutes** and
  keep ~30 for discussion, your questions, and mapping to your next workflows.

---

## The agenda — what we'll show

**1. Your reconciliations, rebuilt with no code (Lakeflow Designer)**
The two workflows you gave us, on a visual drag-and-drop canvas — no desktop ETL tool, no
laptop:
- *Cash matching:* reconcile 40+ bank accounts (ledger vs bank, with the timing/outstanding
  items), each **netting to zero**, and the residual **exceptions flagged** for audit.
- *Control sheet:* split payments into branches and prove every branch **ties back to the main
  total with 0.00 variance**.
Both end in a governed table, and both are **reconciled to the penny** against a coded
benchmark — so you tie the result out, you don't take it on trust.

**2. Trust it, and work on it together**
- Build the same flow by **drag-and-drop** *or* by typing **one plain-English prompt** — your
  choice; no SQL required.
- **See and amend the code:** the flow is real, versioned code underneath. Hand your
  no-code flow to a more technical colleague who tightens the SQL directly — their change
  **reflects straight back into your visual canvas**.
- **Co-edit the same flow** with a colleague live (one governed source of truth, every change
  versioned — not a file emailed around in fifteen versions).
- Automatic **lineage**, **version history / roll-back**, and a one-click **schedule**.

**3. Automate and audit it (the part Designer isn't for)**
Your two Python automations — the file-staging job and the fixed-width parse + contra check —
as **scheduled Databricks Jobs + Autoloader**, running autonomously with no licensed user in
the loop, and a full **audit trail** (run history + Unity Catalog audit) for compliance. This
is the direct answer to your question: *yes, the platform schedules and logs comparably — and
these belong in Jobs, not Designer.*

**4. Ask and forecast your book (the wider platform)**
Beyond the reconciliations — the analytics and forecasting questions you listed:
- **Genie:** ask your book questions in plain English (conversion, renewals, retention,
  segments…) — it writes and runs the SQL, and explains itself.
- A live **AI/BI dashboard** on the same governed data.
- **Forecasting** (built-in `ai_forecast`): next-period volumes, renewal likelihood, targets.

---

## Run of show (~60 minutes)

| Time | Item | What happens |
|---|---|---|
| 0:00–0:04 | **Open** | Recap your requirements; frame the two questions we'll answer — *is it accessible for non-coders?* and *can we trust it?* |
| 0:04–0:22 | **1 · Reconciliations on Designer** | Build cash matching live (join → reconcile → exceptions), run parity → ✅ to the penny. Then the control sheet (branches → tie back to 0.00 variance). |
| 0:22–0:34 | **2 · Trust & collaboration** | Rebuild a step from one prompt; open the code pane and have a "technical colleague" amend the SQL → canvas updates; co-edit + show lineage/version history/schedule. |
| 0:34–0:44 | **3 · Automate & audit** | The file-staging + fixed-width/contra jobs as scheduled Jobs + Autoloader; show the run history + audit log. |
| 0:44–0:59 | **4 · Ask & forecast** | Genie answering your analytics questions live; the dashboard; the forecasting outputs. |
| 0:59–1:04 | **Close** | Agree your next workflows to build, sandbox access, and the follow-up. |

*(~64 min of content; trim item 4 first if running long — it's the "there's more" chapter, not the core. The core is items 1–3, your own workflows.)*

---

## What each item proves (mapped to what you asked for)

| Your requirement / question | Where it's answered |
|---|---|
| Cash matching reconciliation (nets to zero, exceptions) | Item 1 |
| Control-sheet branch reconciliation (0.00 variance) | Item 1 |
| "Accessible for non-coders?" | Items 1–2 (no-code build, prompt build, no SQL to read) |
| "Can we trust AI-generated SQL?" | Items 1–2 (parity to the penny; view/amend the code; fully manual path) |
| "Can a colleague QA / co-own it?" | Item 2 (code hand-off + co-edit) |
| "Scheduled automation & audit logging like our scripts?" | Item 3 (Jobs + Autoloader + UC audit) |
| Handling file drops / new columns | Item 3 (Autoloader) |
| The analytics question set (quotes, conversion, renewals, lapses, book) | Item 4 (Genie + dashboard) |
| The forecasting question set | Item 4 (`ai_forecast`) |

---

## To confirm tomorrow (the 30-minute session)

1. **Which examples do we build against?** Your cash-matching and control-sheet workflows are
   ready as generic, synthetic reproductions — confirm they're representative, or send tweaks.
2. **Priorities & timing:** items 1–3 (your workflows) are the core; item 4 is the wider story —
   keep, trim, or split to a follow-up?
3. **Data:** happy with synthetic reproductions, or do you want us to shape them to your real
   schemas (sample files / column lists)?
4. **Sandbox:** confirm environment + who from your side gets hands-on afterwards.
5. **Date & attendees** for next week.

---

## Assets (for the account team)

- **Designer Recon Accelerator** (items 1–3): repo `wryszka/designer-recon-accelerator` ·
  run doc *"Designer Recon Accelerator — Runbook"* · DEV schema `designer_recon_demo`.
- **Finance Analytics Accelerator** (item 4): repo `wryszka/finance-analytics-accelerator` ·
  run doc *"Finance Analytics Accelerator — Runbook"* · Genie space + dashboard on DEV,
  schema `finance_analytics_demo`.
- Both are in the workbench hub's **Small projects**; both run docs are in the shared Drive folder.

*All data synthetic. Desktop ETL tools referenced as a workflow shape, not a product comparison.*
