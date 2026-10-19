# The workbook: tabs, columns and who fills them

One `.xlsx` file. Tab names and column headers are a contract with `scripts/lcs.py`: rename a header and the script can no longer find it.

| Tab | Filled by | What it holds |
|---|---|---|
| 0 Process | `init`, `dashboard` | The 11 steps with live counts |
| Dashboard | `dashboard` | Funnel from connections to leads, final-run progress |
| 1 Connections | `init` | The raw export, never edited again |
| 2 Rules | `init` | Keyword lists, weights, thresholds (edit the JSON, then re-run init on a copy) |
| 3 Scored | `init` | One row per profile URL: flags, Fit Score, Offer Group, Tier, Reason, Opening Angle |
| 4 First-pass Groups | (optional summary) | Counts by offer and tier, read from 3 Scored |
| 5 Enrichment Log | `batch`, then `merge` | Frozen batches + everything learned in steps 5 and 6 |
| 6a / 6b / 6c | `split`, then `fill` | Qualified leads per offer, P1 first |
| 7 Partnerships | `split`, then `fill` | Content partners and AI peers |
| 8 Excluded | `split` | Checked and not a fit, with the reason |
| Data Sources | `log` | One row per paid run: provider, job, hits, misses, cost |

## 5 Enrichment Log columns (headers on row 4)

Batch, Batch Row, Src Row, Offer Group, Tier, Fit Score, First Name, Last Name, Position, Company, LinkedIn URL, Connected On, Warmth, Opening Angle, **Enriched** (Pending, Yes, No, Failed), Location, Current Title (verified), Company LinkedIn URL, Industry, Headcount, Followers, Latest Post Date, Latest Post Topic, Intent Signal, Est. Revenue Band, **Final Offer Group**, **Final Verdict** (Qualified, Maybe, Not fit, Partner), Notes, Intent Strength, Intent Evidence (quote, date), Evidence Post URL, Intent Source, Hook, Pain Hypothesis, Segment, Language, Brief Status (Ready, Thin), Website, What They Say They Do (About), Background (past roles), In Current Role Since, Profile Languages, Company Notes (description, tech, growth), DM Priority (P1 to P4).

## Lead tab columns (headers on row 6, data from row 7)

| Group | Columns |
|---|---|
| LEAD | Priority, First Name, Last Name |
| CONTACT & PROFILE | LinkedIn URL, Company, Title (verified), Location, Language, Batch, Source Row |
| FIT | Offer, Segment, Revenue Band (est.), Headcount, Followers, Industry, Company LinkedIn, Website, Warmth, Connected On |
| WHY NOW (intent) | Intent Strength, Intent Signal, Evidence Quote (date), Evidence Post URL, Latest Post Date, Latest Post Topic |
| DM BRIEF | Hook, Pain Hypothesis, Intent Source, Brief Status, About (one line), Background (past roles), In Role Since, Profile Languages, Company Notes, Notes & Cautions |
| FINAL RUN (orange) | Website Scrape, Email, Email Status, LinkedIn DM Copy, DM Follow-up 1 (Day 3-4), DM Follow-up 2 (Day 7-10), Cold Email Subject, Cold Email Copy, Cold Email Follow-up 1 (Day 3), Cold Email Follow-up 2 (Day 7), Send Rule, Approved |

`split` rebuilds the lead tabs from the Enrichment Log but keeps every FINAL RUN cell already written, matched on LinkedIn URL, so re-qualifying never wipes finished copy.

## JSON shape for `merge` and `fill`

A list of objects. `LinkedIn URL` is the key; every other key is an exact column header. Empty values are skipped, so a partial update never blanks a cell.

```json
[{"LinkedIn URL": "https://www.linkedin.com/in/example", "Website Scrape": "Sells ...", "Email Status": "not found"}]
```
