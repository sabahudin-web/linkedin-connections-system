#!/usr/bin/env python3
"""LinkedIn Connections System: one local .xlsx from raw export to written DMs and cold emails.

Commands (run with python3, needs openpyxl):
  preview   --connections Connections.csv [--rules rules.json] [--sample 50]   (score a sample, print counts, write nothing)
  init      --connections Connections.csv --out leads.xlsx [--rules rules.json] [--today YYYY-MM-DD]
  batch     --xlsx leads.xlsx --name B1 --tiers A [--offers "Build It Yourself,Done For You"] [--limit 50] [--worklist out.json]
  merge     --xlsx leads.xlsx --json enrichment.json        (rows keyed by "LinkedIn URL", fills 5 Enrichment Log)
  split     --xlsx leads.xlsx                               (builds 6a/6b/6c, 7 Partnerships, 8 Excluded)
  fill      --xlsx leads.xlsx --json copy.json              (website, email, DMs, cold email into the lead tabs)
  worklist  --xlsx leads.xlsx --tab 6a [--need email|copy] [--out work.json]
  log       --xlsx leads.xlsx --json run.json               (appends one Data Sources row)
  dashboard --xlsx leads.xlsx                               (recomputes Dashboard and Process numbers)
  export    --xlsx leads.xlsx --tab 6a --csv out.csv
  demo      --out demo.xlsx                                 (fake people only, for screen recordings)

Every command is safe to re-run: rows are matched on the cleaned LinkedIn URL, filled cells are never
blanked by an empty value, and the raw 1 Connections tab is never changed after init.
"""
import argparse, csv, json, os, re, sys, unicodedata
from datetime import date, datetime

try:
    from openpyxl import Workbook, load_workbook
    from openpyxl.styles import Alignment, Font, PatternFill
    from openpyxl.utils import get_column_letter
except ImportError:
    sys.exit("openpyxl is missing. Run: pip3 install openpyxl")

HERE = os.path.dirname(os.path.abspath(__file__))
NAVY, ORANGE, GREEN, PINK, GOLD, GREY = "1F2F57", "B85C00", "2E5E1F", "E9D2DE", "7A5C00", "F2F2F2"
LETTERS = "A-Za-zÀ-ÖØ-öø-ɏЀ-ӿ"

ENRICH_COLS = ["Batch", "Batch Row", "Src Row", "Offer Group", "Tier", "Fit Score", "First Name", "Last Name",
               "Position", "Company", "LinkedIn URL", "Connected On", "Warmth", "Opening Angle", "Enriched",
               "Location", "Current Title (verified)", "Company LinkedIn URL", "Industry", "Headcount", "Followers",
               "Latest Post Date", "Latest Post Topic", "Intent Signal", "Est. Revenue Band", "Final Offer Group",
               "Final Verdict", "Notes", "Intent Strength", "Intent Evidence (quote, date)", "Evidence Post URL",
               "Intent Source", "Hook", "Pain Hypothesis", "Segment", "Language", "Brief Status", "Website",
               "What They Say They Do (About)", "Background (past roles)", "In Current Role Since",
               "Profile Languages", "Company Notes (description, tech, growth)", "DM Priority"]

LEAD_GROUPS = [
    ("LEAD", NAVY, ["Priority", "First Name", "Last Name"]),
    ("CONTACT & PROFILE", NAVY, ["LinkedIn URL", "Company", "Title (verified)", "Location", "Language", "Batch",
                                 "Source Row"]),
    ("FIT", GREEN, ["Offer", "Segment", "Revenue Band (est.)", "Headcount", "Followers", "Industry",
                    "Company LinkedIn", "Website", "Warmth", "Connected On"]),
    ("WHY NOW (intent)", GOLD, ["Intent Strength", "Intent Signal", "Evidence Quote (date)", "Evidence Post URL",
                                "Latest Post Date", "Latest Post Topic"]),
    ("DM BRIEF (personalisation)", "5A1E3C", ["Hook", "Pain Hypothesis", "Intent Source", "Brief Status",
                                              "About (one line)", "Background (past roles)", "In Role Since",
                                              "Profile Languages", "Company Notes", "Notes & Cautions"]),
    ("FINAL RUN (steps 8 to 11)", ORANGE, ["Website Scrape", "Email", "Email Status", "LinkedIn DM Copy",
                                           "DM Follow-up 1 (Day 3-4)", "DM Follow-up 2 (Day 7-10)",
                                           "Cold Email Subject", "Cold Email Copy", "Cold Email Follow-up 1 (Day 3)",
                                           "Cold Email Follow-up 2 (Day 7)", "Send Rule", "Approved"]),
]
LEAD_COLS = [c for _, _, cols in LEAD_GROUPS for c in cols]
FINAL_COLS = LEAD_GROUPS[-1][2]
ENRICH_TO_LEAD = {"Current Title (verified)": "Title (verified)", "Src Row": "Source Row",
                  "Final Offer Group": "Offer", "Est. Revenue Band": "Revenue Band (est.)",
                  "Company LinkedIn URL": "Company LinkedIn", "Intent Evidence (quote, date)": "Evidence Quote (date)",
                  "What They Say They Do (About)": "About (one line)", "In Current Role Since": "In Role Since",
                  "Company Notes (description, tech, growth)": "Company Notes", "Notes": "Notes & Cautions",
                  "DM Priority": "Priority"}

# ---------- helpers ----------

def clean_url(u):
    u = (u or "").strip().split("?")[0].rstrip("/").lower()
    return re.sub(r"^https?://([a-z]{2,3}\.)?linkedin\.com", "https://www.linkedin.com", u)

def norm(s):
    return unicodedata.normalize("NFC", (s or "").strip().lower())

def build_re(words):
    if not words:
        return None
    alt = "|".join(re.escape(norm(w)) for w in sorted(words, key=len, reverse=True))
    return re.compile(r"(?<![%s])(?:%s)(?![%s])" % (LETTERS, alt, LETTERS), re.I)

def hit(rx, text):
    return bool(rx and rx.search(norm(text)))

def clean_name(n):
    n = re.sub(r"[\U0001F000-\U0001FAFF☀-➿]", "", n or "")
    n = re.sub(r",.*$", "", n)  # credentials after a comma
    n = re.sub(r"\b(PhD|MBA|CPA|ACCA|CIPD|MSc|BSc|MA|Dr\.?)\b", "", n, flags=re.I)
    n = re.sub(r"\s+", " ", n).strip(" -|")
    return n or (n or "").strip()

def parse_date(s):
    s = (s or "").strip()
    for fmt in ("%d %b %Y", "%Y-%m-%d", "%m/%d/%Y", "%d/%m/%Y", "%b %d, %Y"):
        try:
            return datetime.strptime(s, fmt).date()
        except ValueError:
            pass
    return None

def load_rules(path):
    with open(path or os.path.join(HERE, "rules_default.json"), encoding="utf-8") as f:
        return json.load(f)

def style_header(ws, row, ncols, fill=NAVY):
    for c in range(1, ncols + 1):
        cell = ws.cell(row=row, column=c)
        cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = PatternFill("solid", fgColor=fill)
        cell.alignment = Alignment(wrap_text=True, vertical="center")

def title(ws, text, sub):
    ws["A1"] = text
    ws["A1"].font = Font(bold=True, size=16, color=NAVY)
    ws["A2"] = sub
    ws["A2"].font = Font(italic=True, color="555555")

def widths(ws, w=18, wide=None):
    for i in range(1, ws.max_column + 1):
        ws.column_dimensions[get_column_letter(i)].width = w
    for col, val in (wide or {}).items():
        ws.column_dimensions[col].width = val

def sheet_rows(ws, header_row):
    """Return (headers, list of dicts with _row) for a tab whose headers sit on header_row."""
    headers = [c.value for c in ws[header_row]]
    out = []
    for r in range(header_row + 1, ws.max_row + 1):
        vals = [ws.cell(row=r, column=i + 1).value for i in range(len(headers))]
        if not any(v not in (None, "") for v in vals):
            continue
        d = {h: v for h, v in zip(headers, vals) if h}
        d["_row"] = r
        out.append(d)
    return headers, out

def recreate(wb, name, index=None):
    if name in wb.sheetnames:
        index = wb.sheetnames.index(name) if index is None else index
        del wb[name]
    return wb.create_sheet(name, index)

# ---------- scoring ----------

def score_connections(rows, rules, today):
    L = {k: build_re(v) for k, v in rules["lists"].items() if k != "solo_company_exact"}
    solo_exact = set(norm(x) for x in rules["lists"]["solo_company_exact"])
    W, T, offers = rules["weights"], rules["thresholds"], rules["offers"]
    buyer = rules.get("buyer") or {"type": "owner"}
    role_mode = buyer.get("type") == "role"
    target_rx = build_re(buyer.get("target_titles") or [])
    if role_mode and not target_rx:
        sys.exit("rules: buyer.type is 'role' but buyer.target_titles is empty. List the job titles that buy.")
    role_offer = offers[buyer.get("role_offer", "partner")]["label"] if role_mode else None
    company_counts = {}
    for r in rows:
        c = norm(r.get("Company"))
        if c and c not in solo_exact:
            company_counts[c] = company_counts.get(c, 0) + 1
    seen, out = set(), []
    for i, r in enumerate(rows, start=2):
        url = clean_url(r.get("URL"))
        if not url:
            continue
        first, last = clean_name(r.get("First Name")), clean_name(r.get("Last Name"))
        first, last = first or (r.get("First Name") or ""), last or (r.get("Last Name") or "")
        pos, comp = r.get("Position") or "", r.get("Company") or ""
        both = pos + " | " + comp
        dup = url in seen
        seen.add(url)
        d = parse_date(r.get("Connected On"))
        days = (today - d).days if d else None
        warmth = "Unknown" if days is None else ("Hot (0-90d)" if days <= T["hot_days"] else
                                                  "Warm (91-365d)" if days <= T["warm_days"] else "Cold (365d+)")
        f = {
            "exclude": hit(L["exclude"], pos),
            "big": hit(L["big_company"], comp) and buyer.get("exclude_big_company", True),
            "target": role_mode and hit(target_rx, pos),
            "peer": hit(L["peer"], both),
            "false_owner": hit(L["false_owner"], pos),
            "employee": hit(L["employee_title"], pos),
            "solo_title": hit(L["solo_expert"], pos),
            "self_employed": norm(comp) in solo_exact,
            "own_name": bool(last and len(last) > 2 and norm(last) in norm(comp)),
            "team": hit(L["team_business"], both),
            "local": hit(L["local_traditional"], both),
            "colleagues": company_counts.get(norm(comp), 0) >= T["colleague_count"],
        }
        strong, weak = hit(L["strong_owner"], pos), hit(L["weak_owner"], pos)
        f["owner"] = (strong or (weak and not f["employee"])) and not f["false_owner"]
        team = f["team"] or f["local"] or f["colleagues"]
        # an own-name company ("Calloway & Reed Accountants") is a solo sign only when nothing says team
        solo = f["solo_title"] or f["self_employed"] or (f["own_name"] and not team)
        score = (W["owner"] * (f["owner"] or f["target"]) + W["solo_title"] * f["solo_title"]
                 + W["solo_company"] * (f["self_employed"] or f["own_name"])
                 + W["team_or_local"] * (f["team"] or f["local"]) + W["colleagues"] * f["colleagues"]
                 + (W["hot"] if warmth.startswith("Hot") else W["warm"] if warmth.startswith("Warm") else 0))
        if dup:
            group, reason = "Duplicate", "same profile URL appears earlier"
        elif f["exclude"]:
            group, reason = "Out", "student, job seeker or retired"
        elif f["big"]:
            group, reason = "Out", "big-company staff"
        elif f["peer"]:
            group, reason = "AI Peer", "builds AI or automation themselves"
        elif f["target"]:
            group, reason = role_offer, "job title the user sells to"
        elif (f["employee"] or f["false_owner"]) and not f["owner"]:
            group, reason = "Out", "employee title"
        elif f["owner"] and solo and team:
            group, reason = offers["either"]["label"], "owner with solo and team signals"
        elif f["owner"] and team:
            group, reason = offers["partner"]["label"], "owner of a team business"
        elif solo:
            group, reason = offers["self_build"]["label"], "solo expert"
        elif f["owner"]:
            group, reason = "Review", "owner, business type unclear"
        elif not pos.strip():
            group, reason = "Out", "blank title"
        else:
            group, reason = "Review", "no owner word, business type unclear"
        in_offer = group in [o["label"] for o in offers.values()]
        tier = ("A" if score >= T["tier_a"] else "B" if score >= T["tier_b"] else "C") if in_offer else ""
        angle = next((o["angle"] for o in offers.values() if o["label"] == group), "")
        out.append({"Src Row": i, "First Name (clean)": first, "Last Name (clean)": last, "LinkedIn URL": url,
                    "Company": comp, "Position": pos, "Email": r.get("Email Address") or "",
                    "Connected On": d.isoformat() if d else (r.get("Connected On") or ""),
                    "Days Since Connected": days if days is not None else "", "Warmth": warmth,
                    "Duplicate?": "Yes" if dup else "", "Exclude?": "Yes" if f["exclude"] else "",
                    "Big Co?": "Yes" if f["big"] else "", "Peer?": "Yes" if f["peer"] else "",
                    "Owner?": "Yes" if f["owner"] else "", "Solo-Expert Title?": "Yes" if f["solo_title"] else "",
                    "Self-Employed?": "Yes" if f["self_employed"] else "",
                    "Own-Name Company?": "Yes" if f["own_name"] else "",
                    "Team/Local Words?": "Yes" if (f["team"] or f["local"]) else "",
                    "Colleagues in Network": company_counts.get(norm(comp), 0) if comp else 0,
                    "Fit Score": score, "Offer Group": group, "Tier": tier, "Reason": reason,
                    "Opening Angle": angle})
    return out

# ---------- commands ----------

def read_linkedin_csv(path):
    with open(path, encoding="utf-8-sig", newline="") as f:
        lines = f.read().splitlines()
    start = next((i for i, l in enumerate(lines) if l.startswith("First Name")), None)
    if start is None:
        sys.exit("No 'First Name' header found. Is this the LinkedIn Connections.csv export?")
    return list(csv.DictReader(lines[start:]))

def cmd_preview(a):
    """Score a sample of the export with the rules, print counts and example titles per group. Writes nothing."""
    rules = load_rules(a.rules)
    today = datetime.strptime(a.today, "%Y-%m-%d").date() if a.today else date.today()
    raw = read_linkedin_csv(a.connections)
    step = max(1, len(raw) // a.sample) if a.sample else 1
    sample = raw[::step][: a.sample] if a.sample else raw
    scored = score_connections(sample, rules, today)
    groups = {}
    for s in scored:
        groups.setdefault(s["Offer Group"], []).append(s)
    buyer = (rules.get("buyer") or {}).get("type", "owner")
    print(f"Rules preview: {len(scored)} of {len(raw)} connections scored, buyer type '{buyer}'. Nothing was written.\n")
    for name, rows in sorted(groups.items(), key=lambda kv: -len(kv[1])):
        print(f"{name}: {len(rows)} ({round(100.0 * len(rows) / max(1, len(scored)))}%)")
        for s in rows[: a.examples]:
            print(f"   - {s['Position'][:70]}  [{s['Reason']}]")
    print("\nIf a buyer landed in Out or Review, change the rules before running init.")


def cmd_init(a):
    rules = load_rules(a.rules)
    today = datetime.strptime(a.today, "%Y-%m-%d").date() if a.today else date.today()
    raw = read_linkedin_csv(a.connections)
    scored = score_connections(raw, rules, today)
    wb = Workbook()
    wb.remove(wb.active)
    for name in ["0 Process", "Dashboard", "1 Connections", "2 Rules", "3 Scored", "4 First-pass Groups",
                 "5 Enrichment Log", "6a", "6b", "6c", "7 Partnerships", "8 Excluded", "Data Sources"]:
        wb.create_sheet(name)
    ws = wb["1 Connections"]
    cols = ["First Name", "Last Name", "URL", "Email Address", "Company", "Position", "Connected On"]
    ws.append(cols)
    for r in raw:
        ws.append([r.get(c, "") for c in cols])
    style_header(ws, 1, len(cols)); ws.freeze_panes = "A2"; widths(ws, 22)
    ws = wb["2 Rules"]
    title(ws, "Rules: edit keywords and weights here", "One word per cell. Re-run `lcs.py init` with --rules to "
          "rescore. Matching is case-insensitive and whole-word.")
    keys = list(rules["lists"].keys())
    for j, k in enumerate(keys, start=1):
        ws.cell(row=4, column=j, value=k.replace("_", " ").title())
        for i, w in enumerate(rules["lists"][k], start=5):
            ws.cell(row=i, column=j, value=w)
    style_header(ws, 4, len(keys))
    j = len(keys) + 2
    ws.cell(row=4, column=j, value="Weight or threshold"); ws.cell(row=4, column=j + 1, value="Value")
    style_header(ws, 4, j + 1)
    for i, (k, v) in enumerate(list(rules["weights"].items()) + list(rules["thresholds"].items()), start=5):
        ws.cell(row=i, column=j, value=k); ws.cell(row=i, column=j + 1, value=v)
    ws.freeze_panes = "A5"; widths(ws, 22)
    ws = wb["3 Scored"]
    h = list(scored[0].keys()) if scored else []
    ws.append(h)
    for s in scored:
        ws.append([s[c] for c in h])
    style_header(ws, 1, len(h)); ws.freeze_panes = "D2"; ws.auto_filter.ref = ws.dimensions; widths(ws, 16)
    ws = wb["5 Enrichment Log"]
    title(ws, "5 · Enrichment Log: every enriched or checked person", "Frozen batches. Paid data lands here and "
          "never moves when the rules change.")
    for j, c in enumerate(ENRICH_COLS, start=1):
        ws.cell(row=4, column=j, value=c)
    style_header(ws, 4, len(ENRICH_COLS)); ws.freeze_panes = "E5"; widths(ws, 16)
    ws = wb["Data Sources"]
    ds = ["Run ID", "When", "Written to", "Provider", "Job or endpoint", "Requested", "Hits", "Misses",
          "Cost (USD)", "Notes"]
    ws.append(ds); style_header(ws, 1, len(ds)); widths(ws, 20)
    wb.properties.title = "LinkedIn Connections System"
    wb.save(a.out)
    a.xlsx = a.out
    cmd_split(a, quiet=True)
    cmd_dashboard(a)
    counts = {}
    for s in scored:
        counts[s["Offer Group"]] = counts.get(s["Offer Group"], 0) + 1
    print(json.dumps({"connections": len(raw), "scored": len(scored), "groups": counts}, ensure_ascii=False))

def cmd_batch(a):
    wb = load_workbook(a.xlsx)
    _, scored = sheet_rows(wb["3 Scored"], 1)
    log = wb["5 Enrichment Log"]
    _, logged = sheet_rows(log, 4)
    done = set(clean_url(r.get("LinkedIn URL")) for r in logged)
    tiers = [t.strip() for t in a.tiers.split(",")]
    offers = [o.strip() for o in a.offers.split(",")] if a.offers else None
    pick = [s for s in scored if s.get("Tier") in tiers and s.get("LinkedIn URL") not in done
            and (offers is None or s.get("Offer Group") in offers)]
    pick.sort(key=lambda s: (-(s.get("Fit Score") or 0), s.get("Days Since Connected") or 99999))
    if a.limit:
        pick = pick[: a.limit]
    nxt = (max([r["_row"] for r in logged]) + 1) if logged else 5
    work = []
    for i, s in enumerate(pick, start=1):
        vals = {"Batch": a.name, "Batch Row": i, "Src Row": s["Src Row"], "Offer Group": s["Offer Group"],
                "Tier": s["Tier"], "Fit Score": s["Fit Score"], "First Name": s["First Name (clean)"],
                "Last Name": s["Last Name (clean)"], "Position": s["Position"], "Company": s["Company"],
                "LinkedIn URL": s["LinkedIn URL"], "Connected On": s["Connected On"], "Warmth": s["Warmth"],
                "Opening Angle": s["Opening Angle"], "Enriched": "Pending"}
        for j, c in enumerate(ENRICH_COLS, start=1):
            if c in vals:
                log.cell(row=nxt, column=j, value=vals[c])
        nxt += 1
        work.append({k: vals[k] for k in ("LinkedIn URL", "First Name", "Last Name", "Company", "Position",
                                           "Offer Group", "Tier")})
    wb.save(a.xlsx)
    if a.worklist:
        with open(a.worklist, "w", encoding="utf-8") as f:
            json.dump(work, f, ensure_ascii=False, indent=1)
    print(json.dumps({"batch": a.name, "frozen": len(work), "worklist": a.worklist}, ensure_ascii=False))

def merge_into(ws, header_row, items, allowed):
    headers, rows = sheet_rows(ws, header_row)
    idx = {clean_url(r.get("LinkedIn URL")): r["_row"] for r in rows}
    col = {h: i + 1 for i, h in enumerate(headers) if h}
    updated, missing = 0, []
    for it in items:
        r = idx.get(clean_url(it.get("LinkedIn URL")))
        if not r:
            missing.append(it.get("LinkedIn URL")); continue
        for k, v in it.items():
            if k == "LinkedIn URL" or k not in col or k not in allowed or v in (None, ""):
                continue
            ws.cell(row=r, column=col[k], value=v)
        updated += 1
    return updated, missing

def cmd_merge(a):
    wb = load_workbook(a.xlsx)
    with open(a.json, encoding="utf-8") as f:
        items = json.load(f)
    n, miss = merge_into(wb["5 Enrichment Log"], 4, items, set(ENRICH_COLS) - {"Batch", "Batch Row", "Src Row"})
    wb.save(a.xlsx)
    print(json.dumps({"updated": n, "not_found": miss}, ensure_ascii=False))

def priority(r):
    p = (r.get("DM Priority") or "").strip()
    if p:
        return p
    strong, ready = (r.get("Intent Strength") or "") in ("Strong", "Medium"), r.get("Brief Status") == "Ready"
    hot = str(r.get("Warmth") or "").startswith(("Hot", "Warm"))
    return "P1" if ready and strong and hot else "P2" if ready and strong else "P3" if ready else "P4"

def lead_tab(wb, name, ttl, who, offer, angle, rows, keep):
    ws = recreate(wb, name)
    title(ws, ttl, "Sorted by Priority (P1 first), then warmth. Orange columns fill in steps 8 to 11.")
    for j, (lab, val) in enumerate([("Who", who), ("Offer", offer), ("Angle", angle),
                                    ("To do", "8) Website scrape  9) Email  10) LinkedIn DM + 2 follow-ups  "
                                     "11) Cold email + 2 follow-ups. Nothing is sent until you approve.")]):
        c = 1 + j * 6
        ws.cell(row=3, column=c, value=lab); ws.cell(row=4, column=c, value=val)
        ws.cell(row=4, column=c).alignment = Alignment(wrap_text=True, vertical="top")
    style_header(ws, 3, 24)
    c = 1
    for g, color, cols in LEAD_GROUPS:
        ws.cell(row=5, column=c, value=g)
        for k in range(c, c + len(cols)):
            ws.cell(row=5, column=k).fill = PatternFill("solid", fgColor=color)
            ws.cell(row=5, column=k).font = Font(bold=True, color="FFFFFF")
        c += len(cols)
    for j, h in enumerate(LEAD_COLS, start=1):
        ws.cell(row=6, column=j, value=h)
    style_header(ws, 6, len(LEAD_COLS), fill="2B3F6B")
    for j, h in enumerate(LEAD_COLS, start=1):
        if h in FINAL_COLS:
            ws.cell(row=6, column=j).fill = PatternFill("solid", fgColor=ORANGE)
    order = {"P1": 1, "P2": 2, "P3": 3, "P4": 4}
    rows.sort(key=lambda r: (order.get(priority(r), 5), str(r.get("Warmth") or "Z")))
    for i, r in enumerate(rows, start=7):
        lead = {"Priority": priority(r), "First Name": r.get("First Name"), "Last Name": r.get("Last Name"),
                "LinkedIn URL": r.get("LinkedIn URL"), "Company": r.get("Company")}
        for k, v in r.items():
            lead.setdefault(ENRICH_TO_LEAD.get(k, k), v)
        lead["Title (verified)"] = r.get("Current Title (verified)") or r.get("Position")
        lead["Offer"] = r.get("Final Offer Group") or r.get("Offer Group")
        lead.update({k: v for k, v in keep.get(clean_url(r.get("LinkedIn URL")), {}).items() if v})
        for j, h in enumerate(LEAD_COLS, start=1):
            v = lead.get(h)
            if v not in (None, ""):
                cell = ws.cell(row=i, column=j, value=v)
                cell.alignment = Alignment(wrap_text=True, vertical="top")
    ws.freeze_panes = "D7"
    ws.auto_filter.ref = "A6:%s%d" % (get_column_letter(len(LEAD_COLS)), max(7, ws.max_row))
    widths(ws, 18, {"AA": 40, "AB": 40, "AK": 45, "AN": 50, "AO": 40, "AP": 40, "AR": 55, "AS": 40, "AT": 40})
    return len(rows)

def cmd_split(a, quiet=False):
    wb = load_workbook(a.xlsx)
    rules = load_rules(getattr(a, "rules", None))
    offers = rules["offers"]
    _, logged = sheet_rows(wb["5 Enrichment Log"], 4)
    keep = {}
    for name in ["6a", "6b", "6c", "7 Partnerships"]:
        if name in wb.sheetnames and wb[name].max_row >= 6 and wb[name].cell(row=6, column=1).value == "Priority":
            _, rows = sheet_rows(wb[name], 6)
            for r in rows:
                keep[clean_url(r.get("LinkedIn URL"))] = {k: r.get(k) for k in FINAL_COLS}
    counts = {}
    for key in ("self_build", "partner", "either"):
        o = offers[key]
        rows = [r for r in logged if r.get("Final Verdict") == "Qualified"
                and (r.get("Final Offer Group") or r.get("Offer Group")) == o["label"]]
        counts[o["tab"]] = lead_tab(wb, o["tab"], "%s · Leads: %s" % (o["tab"], o["label"]), o["who"],
                                    o["label"], o["angle"], rows, keep)
    part = [r for r in logged if r.get("Final Verdict") == "Partner"]
    counts["7"] = lead_tab(wb, "7 Partnerships", "7 · Partnerships: people who can send you buyers",
                           "Content partners and AI peers.", "No pitch. Referral swap, co-created post or joint offer.",
                           "Your clients keep asking about AI. Want to see if we can send each other work?", part, keep)
    ws = recreate(wb, "8 Excluded", wb.sheetnames.index("7 Partnerships") + 1)
    cols = ["First Name", "Last Name", "LinkedIn URL", "Company", "Position", "Offer Group", "Final Verdict", "Notes"]
    ws.append(cols); style_header(ws, 1, len(cols))
    for r in logged:
        if r.get("Final Verdict") == "Not fit":
            ws.append([r.get(c) for c in cols])
    widths(ws, 22)
    wb.save(a.xlsx)
    if not quiet:
        print(json.dumps(counts))

def cmd_fill(a):
    wb = load_workbook(a.xlsx)
    with open(a.json, encoding="utf-8") as f:
        items = json.load(f)
    total, missing = 0, None
    for name in ["6a", "6b", "6c", "7 Partnerships"]:
        n, miss = merge_into(wb[name], 6, items, set(FINAL_COLS) | {"Website"})
        total += n
        missing = set(miss) if missing is None else missing & set(miss)  # missing only if absent from every tab
    missing = sorted(missing or [])
    wb.save(a.xlsx)
    print(json.dumps({"updated": total, "not_found": missing}, ensure_ascii=False))

def cmd_worklist(a):
    wb = load_workbook(a.xlsx, read_only=True)
    _, rows = sheet_rows(wb[a.tab], 6)
    out = []
    for r in rows:
        if a.need == "email" and (r.get("Email") or r.get("Email Status")):
            continue
        if a.need == "copy" and r.get("LinkedIn DM Copy"):
            continue
        out.append({k: v for k, v in r.items() if k != "_row" and v not in (None, "")})
    data = json.dumps(out, ensure_ascii=False, indent=1, default=str)
    if a.out:
        open(a.out, "w", encoding="utf-8").write(data)
        print(json.dumps({"rows": len(out), "out": a.out}))
    else:
        print(data)

def cmd_log(a):
    wb = load_workbook(a.xlsx)
    with open(a.json, encoding="utf-8") as f:
        run = json.load(f)
    ws = wb["Data Sources"]
    headers = [c.value for c in ws[1]]
    run.setdefault("When", datetime.now().strftime("%Y-%m-%d %H:%M"))
    ws.append([run.get(h, "") for h in headers])
    wb.save(a.xlsx)
    print("logged")

def cmd_dashboard(a):
    wb = load_workbook(a.xlsx)
    rules = load_rules(getattr(a, "rules", None))
    labels = [o["label"] for o in rules["offers"].values()]
    _, scored = sheet_rows(wb["3 Scored"], 1)
    _, logged = sheet_rows(wb["5 Enrichment Log"], 4)
    _, raw = sheet_rows(wb["1 Connections"], 1)
    cnt = lambda rows, f: sum(1 for r in rows if f(r))
    g = lambda name: cnt(scored, lambda r: r.get("Offer Group") == name)
    in_offer = sum(g(l) for l in labels)
    tabs = {}
    for name in ["6a", "6b", "6c", "7 Partnerships"]:
        tabs[name] = sheet_rows(wb[name], 6)[1] if wb[name].max_row >= 7 else []
    leads = sum(len(tabs[t]) for t in ["6a", "6b", "6c"])
    total = len(raw) or 1
    funnel = [
        (1, "Connections exported from LinkedIn", len(raw), "1 Connections"),
        (2, "Have a profile URL (scored)", len(scored), "3 Scored"),
        (2, "  Removed: duplicates", g("Duplicate"), "3 Scored"),
        (2, "  Removed: employees, students, big-company staff, blanks", g("Out"), "3 Scored"),
        (3, "  Set aside: AI Peers (partners, not buyers)", g("AI Peer"), "3 Scored"),
        (3, "  Set aside: Review (business type unclear)", g("Review"), "3 Scored"),
        (3, "In an offer group (%s)" % ", ".join(labels), in_offer, "4 First-pass Groups"),
        (4, "Sent to enrichment", len(logged), "5 Enrichment Log"),
        (5, "  Free pass: judged on title alone, no credits", cnt(logged, lambda r: r.get("Enriched") == "No"), "5"),
        (5, "  Enriched with a provider", cnt(logged, lambda r: r.get("Enriched") == "Yes"), "5"),
        (6, "  Qualified after enrichment", cnt(logged, lambda r: r.get("Final Verdict") == "Qualified"), "5"),
        (7, "Total leads (buyers)", leads, "6a to 6c"),
        (7, "Partnerships", len(tabs["7 Partnerships"]), "7 Partnerships"),
        (7, "Excluded (checked, not a fit)", cnt(logged, lambda r: r.get("Final Verdict") == "Not fit"), "8 Excluded"),
    ]
    ws = recreate(wb, "Dashboard", 1)
    title(ws, "Dashboard: from LinkedIn connections to outreach-ready leads",
          "Run `lcs.py dashboard` after each step to refresh these numbers.")
    ws.append([]); ws.append(["1. Funnel"]); ws["A4"].font = Font(bold=True, size=13, color=NAVY)
    ws.append(["Step", "What happened", "People", "% of connections", "Tab"]); style_header(ws, 5, 5)
    for step, what, n, tab in funnel:
        ws.append([step, what, n, round(100.0 * n / total, 1), tab])
    r0 = ws.max_row + 2
    ws.cell(row=r0, column=1, value="2. Final run progress (filled cells)").font = Font(bold=True, size=13, color=NAVY)
    ws.cell(row=r0 + 1, column=1, value="Step")
    for j, t in enumerate(["6a", "6b", "6c"], start=2):
        ws.cell(row=r0 + 1, column=j, value=t)
    style_header(ws, r0 + 1, 4, ORANGE)
    for k, col in enumerate(["Website Scrape", "Email", "LinkedIn DM Copy", "Cold Email Copy", "Approved"], start=2):
        ws.cell(row=r0 + k, column=1, value=col)
        for j, t in enumerate(["6a", "6b", "6c"], start=2):
            ws.cell(row=r0 + k, column=j, value=cnt(tabs[t], lambda r: r.get(col) not in (None, "")))
    widths(ws, 16, {"B": 58})
    ws = recreate(wb, "4 First-pass Groups", wb.sheetnames.index("3 Scored") + 1)
    title(ws, "4 · First-pass Groups: free keyword scoring of every connection",
          "Groups decide the offer. Tiers decide who gets paid lookups first (A, then B, then C).")
    ws.append([]); ws.append(["Group", "People", "Tier A", "Tier B", "Tier C", "Who they are"])
    style_header(ws, 4, 6)
    for o in rules["offers"].values():
        rows = [r for r in scored if r.get("Offer Group") == o["label"]]
        ws.append([o["label"], len(rows)] + [cnt(rows, lambda r, t=t: r.get("Tier") == t) for t in "ABC"] + [o["who"]])
    for name, who in [("AI Peer", "Build AI or automation themselves: partners, not buyers."),
                      ("Review", "Business type unclear from the title. Check by hand or skip."),
                      ("Out", "Employees, students, job seekers, big-company staff, blank titles.")]:
        ws.append([name, g(name), "", "", "", who])
    widths(ws, 16, {"A": 22, "F": 70})
    ws = recreate(wb, "0 Process", 0)
    title(ws, "0 · Process: how this lead list is built", "Steps 1 to 7 filter and qualify. Steps 8 to 11 write "
          "the outreach. Nothing is sent from this file.")
    steps = [("1", "Export connections", "LinkedIn > Settings > Data privacy > Get a copy of your data > Connections",
              "free", "%d connections" % len(raw)),
             ("2", "Set the rules", "Keyword lists, weights and tier thresholds", "free", "2 Rules"),
             ("3", "Score every connection", "Owner, solo and team signals, warmth, fit score, offer group, tier",
              "free", "%d in an offer group" % in_offer),
             ("4", "Pick what is worth credits", "Freeze a batch by tier before any paid lookup", "free",
              "%d frozen" % len(logged)),
             ("5", "Enrich", "Profile, recent posts, company. Free pass first for clear non-fits",
              "provider credits", "5 Enrichment Log"),
             ("6", "Qualify and brief", "Verdict, intent with a dated quote, hook, pain hypothesis, language",
              "Claude", "Final Verdict column"),
             ("7", "Sort into clean lists", "One tab per offer, priority P1 to P4, partners and excluded apart",
              "free", "%d leads" % leads),
             ("8", "Website scrape", "Services, who they serve, proof, offer, tone in 3 to 5 lines",
              "provider, about $0.0001 a page", "Website Scrape"),
             ("9", "Email", "Work email from name + domain, verified, blank when not found",
              "provider, about $0.004 to $0.009 a lookup", "Email, Email Status"),
             ("10", "LinkedIn DM", "Opener + 2 follow-ups in the lead's language", "Claude", "LinkedIn DM Copy"),
             ("11", "Cold email", "Subject + email + 2 follow-ups, different opening from the DM", "Claude",
              "Cold Email columns")]
    ws.append([]); ws.append(["Step", "Name", "What happens", "Tool and cost", "Result"])
    style_header(ws, 4, 5)
    for s in steps:
        ws.append(list(s))
    widths(ws, 22, {"C": 70})
    wb.save(a.xlsx)
    print(json.dumps({"connections": len(raw), "in_offer": in_offer, "frozen": len(logged), "leads": leads}))

def cmd_export(a):
    wb = load_workbook(a.xlsx, read_only=True)
    headers, rows = sheet_rows(wb[a.tab], 6)
    with open(a.csv, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=[h for h in headers if h], extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow(r)
    print(json.dumps({"rows": len(rows), "csv": a.csv}))

def cmd_demo(a):
    """Fictional people only. Every name, company and domain is invented, domains use .example."""
    path = os.path.join(HERE, "demo_connections.csv")
    a.connections, a.today, a.rules = path, "2026-10-19", None
    cmd_init(a)
    a.xlsx = a.out
    with open(os.path.join(HERE, "demo_enrichment.json"), encoding="utf-8") as f:
        enrich = json.load(f)
    a.name, a.tiers, a.offers, a.limit, a.worklist = "B1", "A,B", None, None, None
    cmd_batch(a)
    a.json = os.path.join(HERE, "demo_enrichment.json"); cmd_merge(a)
    cmd_split(a)
    a.json = os.path.join(HERE, "demo_copy.json"); cmd_fill(a)
    cmd_dashboard(a)

def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("init"); s.add_argument("--connections", required=True); s.add_argument("--out", required=True)
    s.add_argument("--rules"); s.add_argument("--today")
    s = sub.add_parser("preview"); s.add_argument("--connections", required=True); s.add_argument("--rules")
    s.add_argument("--sample", type=int, default=50); s.add_argument("--examples", type=int, default=4); s.add_argument("--today")
    s = sub.add_parser("batch"); s.add_argument("--xlsx", required=True); s.add_argument("--name", required=True)
    s.add_argument("--tiers", default="A"); s.add_argument("--offers"); s.add_argument("--limit", type=int)
    s.add_argument("--worklist")
    for name in ("merge", "fill", "log"):
        s = sub.add_parser(name); s.add_argument("--xlsx", required=True); s.add_argument("--json", required=True)
    s = sub.add_parser("split"); s.add_argument("--xlsx", required=True); s.add_argument("--rules")
    s = sub.add_parser("worklist"); s.add_argument("--xlsx", required=True); s.add_argument("--tab", required=True)
    s.add_argument("--need", choices=["email", "copy"]); s.add_argument("--out")
    s = sub.add_parser("dashboard"); s.add_argument("--xlsx", required=True); s.add_argument("--rules")
    s = sub.add_parser("export"); s.add_argument("--xlsx", required=True); s.add_argument("--tab", required=True)
    s.add_argument("--csv", required=True)
    s = sub.add_parser("demo"); s.add_argument("--out", required=True)
    a = p.parse_args()
    {"preview": cmd_preview, "init": cmd_init, "batch": cmd_batch, "merge": cmd_merge, "split": cmd_split, "fill": cmd_fill,
     "worklist": cmd_worklist, "log": cmd_log, "dashboard": cmd_dashboard, "export": cmd_export,
     "demo": cmd_demo}[a.cmd](a)

if __name__ == "__main__":
    main()
