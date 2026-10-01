# Vireo Audio — ticket re-categoriser

Re-labels every support ticket by what the customer actually wrote (not the intake-bot tag), then charts
monthly volume by true category and by true owning team, and prices the misrouting.

## Run (clean machine, Python 3.9+)
```
pip install -r requirements.txt
mkdir data      # put tickets.csv and agents.csv in ./data  (orders/customers/products are not used)
python vireo.py --data data --out out
```
Takes ~10 seconds. **No API key, no paid calls.** Outputs in `out/`:
`chart_monthly_by_category.png`, `chart_monthly_by_team.png`, `chart_tagged_vs_true.png`,
`monthly_by_category.csv`, `monthly_by_team.csv`, `summary.json` (the numbers), `validation.json`,
`hand_check_sample.csv` (100 random tickets with a blank `human_label` column to fill by hand), `tickets_classified.csv`.

## What it does
1. Loads tickets; shifts legacy (Freshdesk) `resolved_at` +5:30 (UTC -> IST, policy s9). Without this 2,379 of 4,052 legacy tickets resolve *before* they were created.
2. Classifies `customer_message` into 15 topics with ordered keyword rules; maps topic -> owning team using policy s6.
3. Compares tagged team vs true owner; costs the misroute with the policy's own figures (Rs305/transfer, Rs350/SLA breach, Rs290/contact).
4. Checks the rules against an independent signal (the agent's closing note) — see Limits.

## Limits (read these)
- Rules, not a model. Keyword rules miss ~9% of tickets (`unclassified`) and are brittle to new phrasing / Hinglish.
- Agreement between message rules and note-derived labels is only ~69%. Both sides are keyword rules, so this is a consistency check, **not accuracy**. Real accuracy needs the hand-labelled sample.
- No LLM fallback built. First thing to add for the unclassified ~9%.
- Possible Freshdesk re-import duplicates (policy s9) were not removed: no exact duplicates found, near-duplicates not tested.
- Legacy refund amounts are in an unknown native unit (policy s9); refund figures are not used in any headline number.
