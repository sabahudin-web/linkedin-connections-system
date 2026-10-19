#!/usr/bin/env python3
"""Read lead rows from a CSV export of a lead sheet and write DMs back into one column.

The header is found automatically (the first row containing "First Name"), because lead
sheets carry title rows above it. Row numbers are the CSV line numbers, the same numbers
Google Sheets shows, so a DM written to row 7 lands on sheet row 7.

  read   <csv> [--priority P1] [--limit 3] [--only-empty "LinkedIn DM Copy"]
         Prints a JSON list of {"row": n, <column>: value, ...} for non-empty rows.
  write  <csv> <answers.json> [--col "LinkedIn DM Copy"]
         answers.json is {"7": "Hey Lena, ...", "8": "..."}. Writes only that column,
         only those rows, and keeps a one-time backup at <csv>.bak.
"""
import argparse
import csv
import json
import os
import shutil
import sys


def load(path):
    with open(path, newline="", encoding="utf-8-sig") as f:
        rows = list(csv.reader(f))
    for i, r in enumerate(rows):
        if any(c.strip() == "First Name" for c in r):
            return rows, i
    sys.exit("No header row with 'First Name' found. Ask the user which row is the header.")


def cmd_read(a):
    rows, h = load(a.csv)
    header = rows[h]
    out = []
    for i in range(h + 1, len(rows)):
        r = rows[i] + [""] * (len(header) - len(rows[i]))
        rec = {col: r[j] for j, col in enumerate(header) if col}
        if not rec.get("First Name", "").strip():
            continue
        if a.priority and rec.get("Priority", "") != a.priority:
            continue
        if a.only_empty and rec.get(a.only_empty, "").strip():
            continue
        out.append({"row": i + 1, **rec})
        if a.limit and len(out) >= a.limit:
            break
    json.dump(out, sys.stdout, ensure_ascii=False, indent=1)
    print()


def cmd_write(a):
    rows, h = load(a.csv)
    header = rows[h]
    if a.col not in header:
        sys.exit(f"Column '{a.col}' not in header. Ask the user which column to use.")
    j = header.index(a.col)
    answers = json.load(open(a.answers, encoding="utf-8"))
    if not os.path.exists(a.csv + ".bak"):
        shutil.copy(a.csv, a.csv + ".bak")
    n = 0
    for row_s, text in answers.items():
        i = int(row_s) - 1
        if i <= h or i >= len(rows):
            print(f"skip row {row_s}: outside the data rows", file=sys.stderr)
            continue
        rows[i] += [""] * (len(header) - len(rows[i]))
        rows[i][j] = text
        n += 1
    with open(a.csv, "w", newline="", encoding="utf-8") as f:
        csv.writer(f).writerows(rows)
    print(f"wrote {n} cells to '{a.col}'")


p = argparse.ArgumentParser()
sub = p.add_subparsers(dest="cmd", required=True)
r = sub.add_parser("read")
r.add_argument("csv")
r.add_argument("--priority")
r.add_argument("--limit", type=int)
r.add_argument("--only-empty")
r.set_defaults(fn=cmd_read)
w = sub.add_parser("write")
w.add_argument("csv")
w.add_argument("answers")
w.add_argument("--col", default="LinkedIn DM Copy")
w.set_defaults(fn=cmd_write)
a = p.parse_args()
a.fn(a)
