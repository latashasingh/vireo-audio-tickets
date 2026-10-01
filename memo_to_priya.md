# Memo: where to add headcount

**To:** Priya Raman  **cc:** Arjun Mehta, Neha Kulkarni  **Re:** Billing hires — I'd hold them

**Short answer.** Don't give Billing the two hires yet. About 35% of what is tagged "Billing" (891 of 2,564 tickets) isn't a billing problem. It is "I paid, nothing arrived", and the intake bot files it under Billing because the customer mentions paying. Move those to where they belong and the picture flips:

| Team | Tickets as tagged | Tickets by what the customer wrote |
|---|---|---|
| Logistics | 1,905 (16%) | ~3,130 (27%) |
| Billing | 2,564 (22%) | ~2,000 (17%) |

So Neha is right that Logistics is the busy one, and you are right that Billing looks biggest on the export. Both are reading the same bot tag.

**Why it matters in rupees.** A mis-filed delivery ticket is handled by Billing, handed on to Logistics (0.9 hand-offs on average vs 0.09 for tickets that arrive at Logistics directly), and misses its first-response target 36% of the time vs 9%. At the policy's own prices (Rs305 per hand-off, Rs350 per missed target) that is roughly **Rs 0.4 lakh a quarter**, or about **Rs 0.7 lakh** counting the wasted first touch. That is small next to Rs 9 lakh a year for two hires, and Arjun's instinct to fix the process first is right.

**The number to aim for.** Cut mis-filed delivery tickets from 35% of Billing's queue to under 5% by changing the bot's routing rule ("paid" + "not delivered / not received / where is my order" goes to Logistics). Same chart, a month later, tells you if it worked.

**What I would do before hiring.** (1) Fix the bot rule. (2) Re-run this in 4 weeks. (3) If Logistics is still the busiest team and its resolution time stays above a day, put the hires there, not in Billing.

**Two things I changed from your ask.** You asked for volume by team. I also split by what the customer wrote, because the bot tag is the thing in doubt (Sameer says agents rarely re-tag). And the biggest team on the export is actually Chat Frontline (3,030), not Billing; Billing is only the biggest category. Frontline teams are split by channel, so they are not a like-for-like comparison with Billing or Logistics.

**How sure am I.** The 891 is solid: those messages plainly say a paid order did not arrive, and about 800 Billing-tagged tickets were resolved by Logistics agents. The topic labels overall are keyword rules, not a trained model. They agree with the agent's own closing note about 69% of the time. I have not hand-checked accuracy yet, so treat team totals as ±5 points, not exact. Legacy-ticket timestamps were off by 5.5 hours and I corrected them.

**Also spotted, not asked for.** Only 2 tickets show both a refund and a replacement, so the double-refund risk in the policy is small.
