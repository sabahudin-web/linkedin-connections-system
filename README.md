# LinkedIn Connections System

Turn your LinkedIn connections export into a short list of people worth messaging, each with a reason to talk now and the first message already written.

Built and run by Sabahudin Murtic (Unstuck) on his own network: 7,819 connections became 378 qualified leads, every one with a pain hypothesis, a LinkedIn DM, 2 follow-ups and, where a work email was found, a cold email. Nothing is ever sent by the system. You read every message and send it yourself.

## What it does, in 8 steps

1. **Export** your connections from LinkedIn (Settings → Data privacy → Get a copy of your data → Connections).
2. **Cheap filter:** plain keyword rules in 8 languages score every connection. No AI, no credits.
3. **Pick** the tiers worth paying for, frozen as a batch so paid data never shifts.
4. **Enrich** the best tiers with [Loot](https://looot.ai): profile, posts from the last 30 days, company.
5. **Qualify and brief:** a verdict, a dated quote from their own post, a hook, a pain hypothesis.
6. **Sort** into one list per offer, P1 first, plus partners and excluded with the reason.
7. **Final run:** read their website and look for a verified work email.
8. **Write** a LinkedIn DM with 2 follow-ups and a cold email with a subject line and 2 follow-ups.

Everything lives in one local Excel workbook, so it runs from the Claude desktop app. No browser extension or Google Sheets needed.

## Install

It is a Claude skill. Either:

- **Claude Code:** copy this folder to `~/.claude/skills/linkedin-connections-qualifier/`.
- **Claude desktop / claude.ai:** zip this folder and upload it under Settings → Capabilities → Skills.

You also need Python 3 with `openpyxl` (`pip3 install openpyxl`) and, for steps 4, 7 and 8, the Loot connector in Claude with some prepaid credit. An email lookup costs under 1 cent, a website read a fraction of a cent.

Then tell Claude: **"qualify my connections"** and point it at your `Connections.csv`.

## Try it without your data

```bash
python3 scripts/lcs.py demo --out demo-linkedin-connections.xlsx
```

This builds the whole workbook from 50 invented people (fictional names, `.example` domains), so you can see every tab before using your own export.

## What is inside

| File | Job |
|---|---|
| `SKILL.md` | The steps Claude follows |
| `scripts/lcs.py` | Builds and updates the workbook (init, batch, merge, split, fill, worklist, log, dashboard, export, demo) |
| `scripts/rules_default.json` | Keyword lists, weights, tiers and offers. Edit for your own offers |
| `references/loot.md` | The Loot jobs, inputs, costs and what to do on a miss |
| `references/dm-floor.md`, `voice.md` | Rules for the first DM and follow-ups, in your own voice |
| `references/cold-email.md` | Send rule, subject lines, the email and 2 follow-ups |
| `references/reply-engine.md` | What to write when someone replies |
| `references/proof.md` | How to use your own case studies (it ships with none) |
| `references/workbook-tabs.md` | Every tab and column |

## Good to know

- Nothing is sent, posted or launched. You approve and send every message.
- Cold email rules differ by country. The system marks people in Germany and Austria (and UK sole traders) as LinkedIn only. You decide; this is not legal advice.
- No phone numbers or personal emails are copied into the workbook. Only found work emails are, and never an address guessed from a name pattern.

## Want help running it?

The full walkthrough and support live inside the [Unstuck Academy](https://whop.com/unstuck-your-business/products/with-ai-academy/).
