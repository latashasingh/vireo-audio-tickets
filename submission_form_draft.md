# Submission form — DRAFT (edit anything that isn't true for you)

**What did you build, and what business outcome does it move?**
A Python tool that re-labels 11,780 tickets by what the customer wrote and charts monthly volume by true category and team. Finding: 891 of Billing's 2,564 tickets (28%) are "paid, not delivered" delivery issues mis-tagged by the bot. Goal: cut that from 28% to under 5% of Billing's queue. Worth ~Rs 0.4 lakh/quarter (hand-offs + SLA credits), ~Rs 0.7 lakh with wasted first touch. Real value is not hiring 2 people (~Rs 9 lakh/yr) into Billing.

**What does one run cost / a month?**
Rs 0. Rules only, no paid API calls. 650 tickets/week = ~2,800/month; runtime ~10 seconds on a laptop.

**How do you know it works?**
Weakly, and I say so. Compared message-based labels with labels from agents' closing notes on 9,425 tickets: 69% agree. Both are keyword rules, so this is consistency, not accuracy. ~9% of tickets are unclassified. No human-labelled accuracy figure yet. [FILL: if you hand-label hand_check_sample.csv, put the real error rate here.] Typical errors: Hinglish/unusual phrasing, messages mixing payment and delivery.

**Did you change, narrow, or push back on the ask?**
Yes. Added a "true owner" view because the bot tag is the thing in doubt; pointed out the biggest team is Chat Frontline, not Billing; recommended holding the Billing hires.

**What is wrong with what you are handing us?**
Keyword rules, not a model. ~31% disagreement with note-derived labels. No human-labelled test set. No LLM fallback for unclassified. Re-imported duplicate tickets not removed (no exact dups found; near-dups untested). Legacy refund units not decoded, so refund money is not used. Cost per quarter is estimated from a 25-month average. Frontline teams are per-channel, so not comparable with Billing/Logistics. Orders, customers, products files unused.

**What did you deliberately leave out, and why?**
Orders/customers/products joins (lot-code and product defect analysis), CSAT, SLA-by-shift, refund-code audit, legacy currency fix. Chose the routing question because it changes the hiring decision directly.

**Anything built or found that nobody asked for?**
Legacy timestamp bug (resolved_at in UTC, 2,379 tickets resolve before creation). SLA breach rate 36% on mis-routed tickets vs 9%. Refund+replacement double-dip is only 2 tickets.

**What did you use AI for?**
[FILL honestly: Claude (this chat) for exploring data, writing vireo.py, memo draft. Note what you discarded/edited. Add screen-recording link.]

**Someone picks this up on Monday — three things:**
1. The topic rules are in `MSG_RULES` in vireo.py; extend them or add an LLM fallback for `unclassified`.
2. Fill `hand_check_sample.csv` `human_label` to get a real accuracy number.
3. The headline (891 mis-tagged delivery tickets) comes from Billing-tagged + delivery wording; re-run after the bot rule change.

**Honest hours spent:** [FILL — your real number]
**Public Google Drive link:** [FILL]  **GitHub repo link:** [FILL]
