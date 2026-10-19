# Mode A: filling a lead list

## The columns this skill reads

Lead sheets often carry title rows on top. The header is the row holding `First Name`.

| Column | Use it for |
|---|---|
| `Priority` | Order: P1 first. The 3-row test uses the first 3 eligible P1 rows |
| `First Name` | The only merge. Never merge `Company` unless it is clean |
| `Title (verified)`, `About (one line)`, `Company`, `Industry`, `Segment` | Their reality, for the observation line |
| `Offer` | Which of the user's offers the lead fits |
| `Location`, `Language` | Geography check; the language to write in |
| `Latest Post Topic`, `Hook`, `Evidence Quote (date)` | The one true thing. Use the tension behind it, never quote it or say "your post" |
| `Pain Hypothesis` | The likely bottleneck. A guess: shape the question around it, never state it as fact |
| `Website Scrape`, `Company Notes` | What the business sells and how they work |
| `Notes & Cautions` | Read every time. Hardship, regulated work, "same company", "wait" → `HOLD` |
| `Warmth`, `Connected On` | Already connected? Then no "glad we connected" |
| `LinkedIn DM Copy`, `DM Follow-up 1 (Day 3-4)`, `DM Follow-up 2 (Day 7-10)` | **The only columns you write** |

## Where the list lives

### A workbook from `linkedin-connections-system`

1. `python3 <that skill>/scripts/lcs.py worklist --xlsx <file> --tab 6a --need copy --out work.json` lists the rows still without a DM.
2. Draft, self-check, show the 3-row test in chat.
3. After the yes, write a JSON list keyed by `LinkedIn URL` with the three DM columns and run `python3 <that skill>/scripts/lcs.py fill --xlsx <file> --json copy.json`. It never blanks a filled cell.

### A CSV

1. Read rows: `python3 scripts/sheet_rows.py read <file.csv> --priority P1 --limit 3 --only-empty "LinkedIn DM Copy"`
2. Draft, self-check, show the 3 drafts in chat.
3. After the yes, save `{"<row>": "<dm>", ...}` to a JSON file and run `python3 scripts/sheet_rows.py write <file.csv> <answers.json>` (add `--col "DM Follow-up 1 (Day 3-4)"` for a follow-up column). It writes only that column, only those rows, and keeps a one-time `.bak`.
4. Write `SKIP: <reason>` or `HOLD: <reason>` into the cell for skipped rows, so the next run does not redo them.

### A Google Sheet

Export it as CSV, use the CSV flow, and import the column back. Or, inside the Claude extension for Google Sheets, follow the same 3-row test and write only the DM cells. Never write to a shared sheet the user has not pointed at.

## What a filled cell looks like (shape only, placeholder lead)

```
Hey {first_name}, running the coaching and the content alone means one of them slips on a full week. Which one goes first for you?
```

Under 300 characters. One question. No link. No offer. No "your post". In a real cell, write their actual first name, not the token, unless the sheet feeds a merge tool.
