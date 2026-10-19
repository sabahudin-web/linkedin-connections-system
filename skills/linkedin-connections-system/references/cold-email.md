# Step 11: the cold email, its subject line and two follow-ups

Only for leads with a found work email. The email is a second door, not a copy of the DM: a different opening, the same honest reason to talk. Nothing in this file sends anything. The skill writes drafts into the workbook; the user sends from their own tool after approving each row.

## Send Rule (column Send Rule), decided first

Write one of these per row before any copy:

| Send Rule | When |
|---|---|
| `DM first, email day 3` | Default when both exist. Email only if the DM got no reply. |
| `Email only` | No LinkedIn reply possible (they rarely log in, last post over 6 months ago). |
| `LinkedIn only` | No email found, or the email is risky / invalid. |
| `LinkedIn only (check consent rules)` | The person is in Germany or Austria, or is a UK sole trader or partnership. Those places usually need prior consent for marketing email, even to business addresses. The user decides; the skill does not give legal advice. |

Every email carries who is writing and a one-line way to opt out. Recipients in the US: the sender's postal address goes in the signature.

## Subject line (column Cold Email Subject)

1. 2 to 5 words, lowercase, no emoji, no punctuation tricks, no "Re:" on a first email.
2. About them, not you: their thing, their number, their words. It should look like an email a colleague would send.
3. Write 3 options from the patterns below, then keep the one that only this person could receive. Put the other two after it in brackets for the user: `the cv promise [alt: 30 years, then solo / law firm shortlists]`.
4. Banned: "quick question", "quick idea", "following up", "partnership opportunity", their first name alone, anything in capitals, anything that names your offer.

Patterns:

| Pattern | Shape |
|---|---|
| Their number | `316 projects in 59 cities` |
| Their phrase | `the cv promise` |
| Their thing + the topic | `[company] client intake` |
| A question in 3 words | `posts or sessions?` |
| The change | `going solo after 30 years` |
| Mutual context | `from one linkedin connection` |

## The first email (column Cold Email Copy)

50 to 110 words, plain text, no links, no images, no attachments. Four short blocks:

1. **Opening, from the website scrape.** One specific detail from their site that the DM did not use (a service, a client type, a line from their about page). Show you read it.
2. **The bridge.** The `Pain Hypothesis` said as something you noticed is common for businesses like theirs, never as an accusation ("I imagine..." beats "You struggle with...").
3. **One proof line, only if it is real.** One item from the user's proof list (collected in step 0, see `linkedin-dm-writer` `references/proof.md`), matched to their situation. No proof given means no proof line. Never invent a number or a client.
4. **Interest call to action.** One easy question that asks for interest, not for a meeting ("Worth sending you the 2-minute version?"). No calendar link in email 1.

Then the sign-off and the opt-out line: "If this is not relevant, reply 'no' and I will not email again."

## Follow-up 1 (column Cold Email Follow-up 1, Day 3, same thread)

1 to 3 lines. One new thing: a specific idea for their business, a short example, or a sharper version of the question. Never "bumping this" or "just following up".

## Follow-up 2 (column Cold Email Follow-up 2, Day 7, same thread)

Close the loop kindly: the offer to help stands, no reply needed if the timing is wrong. Keep the opt-out line.

## Delivery notes for the user (put in the run report, not in the email)

- Send from a secondary domain that has been warmed up, never the main domain.
- Start low (20 to 30 a day per inbox) and keep the first email link-free.
- Stop the sequence for anyone who replies, on either channel.

## Before saving

Check each row: subject not used for anyone else in the batch, opening detail not the same as the DM's, opt-out line present, word count 50 to 110, language matches the `Language` column.
