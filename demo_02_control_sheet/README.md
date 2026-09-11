# Use Case 2 — Control sheet: branches that tie back to the whole

The classic control: join a category lookup onto a payments dataset, split it into **six or
seven separate tables** by combinations of category and other fields, then a **summary control
sheet that sums the total of each** — and prove the parts tie back to the whole with **zero
variance**. Today it's a desktop-ETL canvas of filters and summaries; here it's a Lakeflow
Designer flow with a governed table out and the reconciliation built in.

## What you'll build
`cs_control_sheet`: per-branch totals plus the main total, with a variance that must be
**0.00**. Sources (synthetic, `cs_` prefix — run `01_generate_sources` first):

| Table | What it is |
|---|---|
| `cs_payments` | payment transactions (the main dataset) |
| `cs_category_lookup` | supplier → category (the VLOOKUP join) |
| `cs_benchmark` | the coded control sheet — `02_parity` proves the canvas matches it |

**Needs:** serverless compute + **Lakeflow Designer** (GA — **+ New → Data prep**).

## Build the canvas
1. **+ New → Data prep** → blank canvas.
2. **Add source** → `cs_payments` and `cs_category_lookup`.
3. **Join** `cs_payments` + `cs_category_lookup`, inner join on `supplier = supplier` — name
   it **lookup category** (the VLOOKUP).
4. **SQL** operator to derive the branch key each payment belongs to:
   ```sql
   SELECT *,
          CASE WHEN category IN ('Claims','Refund','Travel') THEN 'Provider' ELSE 'NonProvider' END
            AS provider_flag,
          CASE WHEN account_id % 2 = 0 THEN 'Img2' ELSE 'Img3' END AS img_group,
          concat(company_code, ' ',
                 CASE WHEN category IN ('Claims','Refund','Travel') THEN 'Provider' ELSE 'NonProvider' END,
                 ' ', CASE WHEN account_id % 2 = 0 THEN 'Img2' ELSE 'Img3' END) AS branch
   FROM lookup_category
   ```
   Name it **assign branch**.
5. **Aggregate** — group by `branch`, sum `amount_paid` → `branch_total` — name it **branch totals**.
6. **SQL** operator to add the main total row and the variance (0.00), matching the control
   sheet shape:
   ```sql
   SELECT branch, round(branch_total, 2) AS branch_total, 0.00 AS variance FROM branch_totals
   UNION ALL
   SELECT 'MAIN (all payments)', round(sum(branch_total), 2), 0.00 FROM branch_totals
   ```
   Name it **control sheet**.
7. **Output** → table `cs_control_sheet`, your catalog / schema → **Run**.

## Alternative — build it with ONE AI prompt (no drag-and-drop)
Paste into the canvas prompt box:
> *Join cs_payments and cs_category_lookup on supplier. Add a branch column = company_code + ' '
> + (Provider if category in Claims/Refund/Travel else NonProvider) + ' ' + (Img2 if account_id
> is even else Img3). Aggregate: group by branch, sum amount_paid as branch_total. Then add a
> row labelled 'MAIN (all payments)' with the sum of all branch_totals, and a variance column
> of 0.00. Write to a table cs_control_sheet in lr_dev_aws_us_catalog.designer_recon_demo.*

## Prove it, then the payoff
- **Run `02_parity`** → **✅ PARITY**: every branch matches the coded control sheet and the
  branches tie back to the main total with **0.00 variance**. That reconciliation is the
  control — you tie it out, not trust the SQL.
- **See & amend the code** (**</> Code**): hand it to an engineer who refines the branch logic
  in the SQL step; the edit reflects back into your canvas.
- **Govern it:** versioned object, lineage back to `cs_payments`, one-click **Schedule**.
- **Co-edit:** **Share** the flow as **Can Edit** with a colleague — one governed source of
  truth, every change versioned.

## About this demo
All data is synthetic — suppliers, companies, banks and payees are generic placeholders. No
real organisation or payee. Desktop ETL is referenced as a workflow *shape*, not a comparison.
