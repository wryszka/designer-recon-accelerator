# Use Case 1 — Cash matching (bank reconciliation), no desktop ETL tool

A period-end reconciliation that today runs in a desktop ETL tool on someone's laptop: pull
the ledger and bank balances, join them per account, work out whether each account nets to
zero once timing items are accounted for, and flag the ones that don't. Here you build it on
a **Lakeflow Designer** canvas — governed table out, real code behind it, lineage and a
schedule, and the exceptions surfaced for the auditor.

## What you'll build
`cm_reconciliation`: GL and bank balances joined per account, with a **variance** and a
**Reconciled / Exception** status. Sources (synthetic, `cm_` prefix — run
`01_generate_sources` first):

| Table | What it is |
|---|---|
| `cm_gl_balances` | ledger/ERP closing balances + outstanding-in-GL items |
| `cm_bank_balances` | bank-feed closing balances + outstanding-on-bank items |
| `cm_accounts` | account reference (name, GL account, house bank, currency) |
| `cm_benchmark` | the coded reconciliation — `02_parity` proves the canvas matches it |

**Needs:** serverless compute + **Lakeflow Designer** (GA — **+ New → Data prep**).

## Build the canvas
1. **+ New → Data prep** → blank canvas.
2. **Add source** → `cm_gl_balances`, `cm_bank_balances`, `cm_accounts` (search `cm_`; point
   the picker at your catalog / schema if empty).
3. **Join** `cm_gl_balances` + `cm_bank_balances`, inner join on `account_code = account_code`
   — name it **match gl to bank**. (Optionally **Join** `cm_accounts` too, to carry the
   account name/currency through.)
4. **SQL** operator on the join — compute the reconciliation and the exception flag:
   ```sql
   SELECT account_code, period, closing_balance_gl, closing_balance_bank,
          os_bank_not_gl, os_gl_not_bank,
          round(closing_balance_gl - (closing_balance_bank + os_bank_not_gl - os_gl_not_bank), 2) AS variance,
          CASE WHEN abs(closing_balance_gl - (closing_balance_bank + os_bank_not_gl - os_gl_not_bank)) < 0.01
               THEN 'Reconciled' ELSE 'Exception' END AS status
   FROM match_gl_to_bank
   ```
   Name it **reconcile**.
5. **Output** → table `cm_reconciliation`, your catalog / schema → **Run**.
   Open the preview: most accounts show `variance` ≈ 0 (`Reconciled`); a few are `Exception`.

## Alternative — build it with ONE AI prompt (no drag-and-drop)
On a blank Data prep canvas, open the **✨ Generate** / prompt box and paste:
> *Add sources cm_gl_balances and cm_bank_balances. Inner join them on account_code. Then a
> SQL step computing variance = round(closing_balance_gl - (closing_balance_bank +
> os_bank_not_gl - os_gl_not_bank), 2) and a status column that is 'Reconciled' when
> abs(variance) < 0.01 else 'Exception', keeping account_code, period and the balance columns.
> Write the result to a table cm_reconciliation in catalog lr_dev_aws_us_catalog, schema
> designer_recon_demo.*

Designer lays out sources → join → SQL → output; review the nodes and **Run**. Same governed
result, no operators clicked, no SQL typed.

## Prove it, then the payoff
- **Run `02_parity`** → **✅ PARITY**: every account matches the coded reconciliation to the
  penny, including which accounts are exceptions. You reconcile the result rather than trust
  the generated SQL.
- **See & amend the code:** click the **</> Code** toggle — the flow is generated SQL. Hand
  it to a more technical colleague who tightens the SQL step directly (e.g. adds a currency
  guard, or `WHERE abs(variance) >= 0.01` to output exceptions only); **their edit reflects
  straight back into your visual canvas**. Edit in either surface, one definition underneath.
- **Govern it:** the flow is a versioned workspace object — commit / review / roll back;
  Catalog Explorer → `cm_reconciliation` → **Lineage** walks back to the sources; **Schedule**
  turns it into a monitored month-end job.
- **Co-edit (you + a colleague):** **Share** the flow with a teammate as **Can Edit** — you're
  both on one governed source of truth, changes are versioned so you can see who changed what.

## About this demo
All data is synthetic and fabricated — accounts, balances and exceptions are invented. No real
organisation, bank or account. A desktop ETL tool is referenced as a workflow *shape*, not a
product comparison.
