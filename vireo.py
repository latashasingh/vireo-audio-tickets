#!/usr/bin/env python3
"""Vireo Audio ticket re-categoriser. No paid API calls: rules on the customer's own words.

Usage: python vireo.py [--data data] [--out out]
Writes: out/tickets_classified.csv, out/monthly_by_category.csv, out/monthly_by_team.csv,
        out/chart_*.png, out/summary.json, out/validation.json
"""
import argparse, json, os, re
import pandas as pd

# ---------- topic -> owning team (support-policy.pdf s6) ----------
OWNER = {
    "payment_duplicate": "Billing", "payment_no_order": "Billing", "invoice_gst": "Billing",
    "promo_price": "Billing",
    "not_delivered": "Logistics", "damaged_wrong_item": "Logistics",
    "cancellation": "Returns Desk", "return_refund": "Returns Desk",
    "warranty_hw": "Escalations & Warranty",
    "connectivity": "Frontline", "charging_battery": "Frontline", "audio_quality": "Frontline",
    "app_firmware": "Frontline", "account_login": "Frontline", "product_enquiry": "Frontline",
    "unclassified": "Frontline",
}

# Ordered rules: first match wins. Applied to customer_message only (what the intake bot could see).
MSG_RULES = [
    ("payment_duplicate", r"double (pay|charg)|charged twice|twice|deducted two|same amount|duplicate (pay|charg|txn)|double payment"),
    ("payment_no_order", r"(deducted|debited|money (went|gone)|page failed|failed after).*(no order|not (show|creat)|nothing|without)|no order|order not showing|payment failed|amount deducted|money debit"),
    ("invoice_gst", r"invoice|gst|\bbill\b|tax receipt"),
    ("promo_price", r"discount|coupon|promo|\d+% off|full price|price drop|price differ|cart says"),
    ("warranty_hw", r"strap|tear|warranty|\brma\b|service cent|sent the unit|repair|touch ?screen|display|screen (is )?(dead|flick|black)|unresponsive|tap ten|swipe"),
    ("damaged_wrong_item", r"damag|crack|broken|different thing|wrong (item|product)|not what i paid|dent|kicked|missing (item|part|cable)|empty box"),
    ("return_refund", r"pickup|pick up|packed the box|waiting for (ur|your) courier|nobody came|\\breturn"),
    ("cancellation", r"cancel|change of mind|stop the shipment|without asking|reverse (the )?order|ordered by mistake"),
    ("not_delivered", r"deliver|not (yet )?(received|rcvd)|haven.?t received|never (got|arrived)|parcel|package|shipment|tracking|courier|something to show up|order status|still says processing|has not moved|paid.{0,20}(then )?nothing|nothing (came|arrived)|stuck|where is my stuff|no idea where|nothing in hand|front door|transaction done|payment went through|since payment|not at (my )?door|nothing in my hand"),
    ("return_refund", r"refund|amount is nowhere|money back"),
    ("connectivity", r"losing my phone|other room|pair|bluetooth|disconnect|wi-?fi|connect|discover|blinks|cutting out|doesn.?t see it|not showing in|drops"),
    ("charging_battery", r"charg|batter|lights up|one earbud|not taking|only the (left|right)|drain|dies|power (on|off)|won.?t turn on|case.*(led|light)"),
    ("audio_quality", r"one ear|one side|mute|music|audio|sound|crackl|static|bass|volume|mic|muffled|distort|noise|hiss"),
    ("app_firmware", r"\bapp\b|firmware|\bfw\b|update|crash|sync"),
    ("account_login", r"login|log in|password|otp|account|sign ?in|email (change|id)"),
    ("product_enquiry", r"compatib|does .* work|work with|will this|can i connect|spec|waterproof|survive|which|how (long|many)|enquir"),
]

# Independent "silver" labels from the agent's closing note (written AFTER the fact, different vocabulary).
NOTE_RULES = [
    ("payment_duplicate", r"duplicate (pay|refund|txn)|double|charged twice|utr"),
    ("payment_no_order", r"without order|failed order|no order|order manually created|amount deducted"),
    ("invoice_gst", r"gst|invoice|gstin"),
    ("promo_price", r"coupon|promo|discount|price"),
    ("not_delivered", r"dlvry|deliver|not rcvd|not received|shipment not|lost in transit|crr|courier partner|awb|re-?ship"),
    ("damaged_wrong_item", r"damag|wrong item|incorrect product|different item|crack"),
    ("cancellation", r"cancel"),
    ("return_refund", r"pickup|refund (pending|delay)|reverse|refund conf|qc"),
    ("warranty_hw", r"rma|wty|warranty|repair|service cent|unresponsive|display"),
    ("connectivity", r"pair|connect|wifi|discover|disconnect"),
    ("charging_battery", r"charg|batter|lights up|one earbud|not taking|only the (left|right)"),
    ("audio_quality", r"one ear|one side|mute|music|audio|sound|crackl|mic|static"),
    ("app_firmware", r"\bapp\b|firmware|fw "),
    ("account_login", r"login|password|otp|account"),
    ("product_enquiry", r"enquiry|compatib|spec sheet|spec"),
]


def _first_match(text, rules):
    s = str(text).lower().replace("\\n", " ")
    s = re.sub(r"expected: ?(refund|replacement|callback|fix)", " ", s)
    for label, pat in rules:
        if re.search(pat, s):
            return label
    return "unclassified"


def load(data):
    t = pd.read_csv(os.path.join(data, "tickets.csv"))
    ag = pd.read_csv(os.path.join(data, "agents.csv"))
    for c in ["created_at", "first_response_at", "resolved_at"]:
        t[c] = pd.to_datetime(t[c])
    # Legacy resolved_at was reconstructed from a UTC event log (policy s9): shift to IST.
    leg = t.source_system == "legacy_fd"
    t.loc[leg & t.resolved_at.notna(), "resolved_at"] += pd.Timedelta(hours=5, minutes=30)
    t["month"] = t.created_at.dt.to_period("M").astype(str)
    # resolving agent's team (use agent_id, never the name: two agents share a display name)
    team = ag.drop_duplicates("agent_id", keep="last").set_index("agent_id")["team"]
    t["resolver_team"] = t.agent_id.map(team)
    t["handle_hours"] = (t.resolved_at - t.first_response_at).dt.total_seconds() / 3600
    target = {"chat": 15 / 60, "voice": 2, "social": 4, "email": 8}
    t["frt_hours"] = (t.first_response_at - t.created_at).dt.total_seconds() / 3600
    t["breach"] = t.frt_hours > t.channel.map(target)
    return t


def classify(t):
    t = t.copy()
    t["true_topic"] = t.customer_message.map(lambda x: _first_match(x, MSG_RULES))
    t["silver_topic"] = t.agent_notes.map(lambda x: _first_match(x, NOTE_RULES))
    t["true_owner"] = t.true_topic.map(OWNER)
    # Frontline topics: keep the channel's frontline team as the owner for charting
    fl = {"chat": "Chat Frontline", "social": "Chat Frontline", "email": "Email Frontline", "voice": "Voice Frontline"}
    t.loc[t.true_owner == "Frontline", "true_owner"] = t.channel.map(fl)
    return t


def validate(t):
    both = t[(t.silver_topic != "unclassified") & (t.true_topic != "unclassified")]
    agree = (both.true_topic == both.silver_topic).mean()
    # Bot tag vs silver, for comparison: how often is the bot's tag consistent with the note?
    bot_map = {"Billing & Payments": {"payment_duplicate", "payment_no_order", "invoice_gst", "promo_price"},
               "Delivery & Shipping": {"not_delivered", "damaged_wrong_item"},
               "Returns & Refunds": {"return_refund", "cancellation"},
               "Warranty & Repair": {"warranty_hw"}, "Connectivity": {"connectivity"},
               "Charging & Battery": {"charging_battery"}, "App & Firmware": {"app_firmware"},
               "Audio Quality": {"audio_quality"}, "Account & Login": {"account_login"},
               "Product Enquiry": {"product_enquiry"}}
    ok = [(r.silver_topic in bot_map[r.category]) for r in both.itertuples() if r.category in bot_map]
    return {
        "n_total": int(len(t)), "n_unclassified_by_message": int((t.true_topic == "unclassified").sum()),
        "n_compared": int(len(both)),
        "message_rules_vs_agent_note_agreement": round(float(agree), 4),
        "bot_tag_vs_agent_note_agreement_excl_Other": round(sum(ok) / max(len(ok), 1), 4),
        "caveat": "Silver labels come from agent notes (also keyword rules, plus agents copy-paste). "
                  "This is a consistency check, NOT human-labelled ground truth. Hand-check sample: see hand_check_sample.csv",
    }


def summarise(t):
    S = {}
    tagged = t.assigned_team.value_counts()
    true = t.true_owner.value_counts()
    S["tagged_team_volume"] = tagged.to_dict()
    S["true_owner_volume"] = true.to_dict()
    S["billing_share_tagged"] = round(float(tagged.get("Billing", 0) / len(t)), 4)
    S["billing_share_true"] = round(float(true.get("Billing", 0) / len(t)), 4)
    S["logistics_share_tagged"] = round(float(tagged.get("Logistics", 0) / len(t)), 4)
    S["logistics_share_true"] = round(float(true.get("Logistics", 0) / len(t)), 4)

    mis = t[(t.assigned_team == "Billing") & (t.true_owner == "Logistics")]
    S["billing_tagged_but_delivery_n"] = int(len(mis))
    S["billing_tagged_but_delivery_pct_of_billing"] = round(len(mis) / max((t.assigned_team == "Billing").sum(), 1), 4)

    # Cost of the misroute (policy s4): Rs305 per transfer, Rs165/agent-hour extra handling, Rs350 SLA credit per breach.
    helpd = t[t.source_system == "helpdesk"]
    m_h = helpd[(helpd.assigned_team == "Billing") & (helpd.true_owner == "Logistics")]
    d_h = helpd[(helpd.assigned_team == "Logistics") & (helpd.true_owner == "Logistics")]
    S["misroute_avg_transfers_helpdesk"] = round(float(m_h.transfers.mean()), 3)
    S["direct_logistics_avg_transfers_helpdesk"] = round(float(d_h.transfers.mean()), 3)
    S["misroute_median_handle_hours"] = round(float(m_h.handle_hours.median()), 2)
    S["direct_logistics_median_handle_hours"] = round(float(d_h.handle_hours.median()), 2)
    S["misroute_breach_rate"] = round(float(m_h.breach.mean()), 4)
    S["direct_logistics_breach_rate"] = round(float(d_h.breach.mean()), 4)
    n_months = t.month.nunique()
    per_q = len(mis) / n_months * 3
    extra_transfers = max(m_h.transfers.mean() - d_h.transfers.mean(), 0)
    extra_breach = max(m_h.breach.mean() - d_h.breach.mean(), 0)
    # wasted first touch: Billing agent re-handles then hands off = one extra contact at blended Rs290
    wasted_touch = 290
    S["misrouted_tickets_per_quarter"] = round(per_q)
    S["rs_per_quarter_transfer"] = round(per_q * extra_transfers * 305)
    S["rs_per_quarter_wasted_first_touch"] = round(per_q * wasted_touch)
    S["rs_per_quarter_extra_sla_credit"] = round(per_q * extra_breach * 350)
    S["rs_per_quarter_total_conservative"] = int(S["rs_per_quarter_transfer"] + S["rs_per_quarter_extra_sla_credit"])
    S["rs_per_quarter_total_with_wasted_touch"] = int(S["rs_per_quarter_total_conservative"] + S["rs_per_quarter_wasted_first_touch"])

    # Double-dip: refund AND replacement on same ticket (policy s5 forbids it)
    dd = t[t.refund_amount_inr.notna() & (t.replacement_issued == "Y")]
    S["refund_and_replacement_same_ticket_n"] = int(len(dd))
    S["refund_and_replacement_same_ticket_rs_refunds"] = float(dd.refund_amount_inr.sum())
    return S


def charts(t, out):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    last = t[t.month >= "2025-01"]
    by_cat = last.pivot_table(index="month", columns="true_topic", values="ticket_id", aggfunc="count", fill_value=0)
    by_cat.to_csv(os.path.join(out, "monthly_by_category.csv"))
    ax = by_cat.plot(kind="bar", stacked=True, figsize=(13, 6), colormap="tab20", width=0.85)
    ax.set_title("Monthly tickets by TRUE topic (from customer's own words)"); ax.set_ylabel("tickets"); ax.legend(fontsize=7, ncol=2)
    plt.tight_layout(); plt.savefig(os.path.join(out, "chart_monthly_by_category.png"), dpi=130); plt.close()

    tm = pd.concat([last.assign(view="Tagged team (as exported)", team=last.assigned_team),
                    last.assign(view="True owner (after re-categorising)", team=last.true_owner)])
    piv = tm.pivot_table(index="month", columns=["view", "team"], values="ticket_id", aggfunc="count", fill_value=0)
    piv.to_csv(os.path.join(out, "monthly_by_team.csv"))
    fig, axes = plt.subplots(1, 2, figsize=(15, 6), sharey=True)
    for a, v in zip(axes, ["Tagged team (as exported)", "True owner (after re-categorising)"]):
        piv[v].plot(kind="bar", stacked=True, ax=a, colormap="tab10", width=0.85); a.set_title(v); a.legend(fontsize=7)
    plt.tight_layout(); plt.savefig(os.path.join(out, "chart_monthly_by_team.png"), dpi=130); plt.close()

    cmp_ = pd.DataFrame({"tagged": t.assigned_team.value_counts(), "true_owner": t.true_owner.value_counts()}).fillna(0)
    cmp_.sort_values("true_owner").plot(kind="barh", figsize=(9, 5)); plt.title("Volume per team: tagged vs true owner")
    plt.tight_layout(); plt.savefig(os.path.join(out, "chart_tagged_vs_true.png"), dpi=130); plt.close()


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--data", default="data"); ap.add_argument("--out", default="out")
    a = ap.parse_args(); os.makedirs(a.out, exist_ok=True)
    t = classify(load(a.data))
    t.drop(columns=["customer_message", "agent_notes"]).to_csv(os.path.join(a.out, "tickets_classified.csv"), index=False)
    t.sample(100, random_state=7)[["ticket_id", "category", "assigned_team", "true_topic", "silver_topic", "customer_message", "agent_notes"]] \
        .assign(human_label="").to_csv(os.path.join(a.out, "hand_check_sample.csv"), index=False)
    json.dump(validate(t), open(os.path.join(a.out, "validation.json"), "w"), indent=2)
    json.dump(summarise(t), open(os.path.join(a.out, "summary.json"), "w"), indent=2)
    charts(t, a.out)
    print(open(os.path.join(a.out, "summary.json")).read()); print(open(os.path.join(a.out, "validation.json")).read())


if __name__ == "__main__":
    main()
