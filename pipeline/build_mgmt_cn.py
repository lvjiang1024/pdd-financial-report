# -*- coding: utf-8 -*-
import json, re, os
from translations import TITLE_TR, SPEAKER_TR, QUOTE_TR

SCRATCH = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(SCRATCH, "data")
Q = json.load(open(os.path.join(DATA_DIR, "quarterly_raw.json")))
M = json.load(open(os.path.join(DATA_DIR, "mgmt_structured.json")))

Qby = {r["quarter"]: r for r in Q}

JUNK_EXACT = {"Monthly active users", "Annual spending per active buyer",
              "Revenue from Contracts with Customers (Topic 606)"}
JUNK_PREFIX = ("Reconciliation of Non",)

def is_junk(txt):
    txt = txt.strip()
    if txt in JUNK_EXACT or txt.startswith(JUNK_PREFIX):
        return True
    if len(txt) < 40 and not re.search(r"\b(we|our|i|this|the)\b", txt, re.I):
        return True
    return False

def fmt_m(v):
    if v is None:
        return None
    return f"{v:,.1f}"

def cn_bullets(r):
    """Build clean Chinese highlight bullets directly from verified numeric fields."""
    b = []
    if r.get("revenue") is not None:
        b.append(f"本季度营业收入为人民币{fmt_m(r['revenue'])}百万元。")
    if r.get("rev_marketing") is not None and r.get("rev_transaction") is not None:
        b.append(f"其中，在线营销服务及其他收入为人民币{fmt_m(r['rev_marketing'])}百万元，交易服务收入为人民币{fmt_m(r['rev_transaction'])}百万元。")
    elif r.get("rev_marketing") is not None:
        b.append(f"其中，在线营销服务收入为人民币{fmt_m(r['rev_marketing'])}百万元。")
    def signed_amt(v):
        if v is None:
            return None
        return f"{'亏损' if v < 0 else ''}人民币{fmt_m(abs(v))}百万元"

    if r.get("operating_profit") is not None:
        parts = [f"本季度营业利润（GAAP）为{signed_amt(r['operating_profit'])}"]
        if r.get("nongaap_operating_profit") is not None:
            parts.append(f"Non-GAAP营业利润为{signed_amt(r['nongaap_operating_profit'])}")
        b.append("，".join(parts) + "。")
    if r.get("net_income") is not None:
        parts = [f"归母净利润（GAAP）为{signed_amt(r['net_income'])}"]
        if r.get("nongaap_net_income") is not None:
            parts.append(f"Non-GAAP归母净利润为{signed_amt(r['nongaap_net_income'])}")
        b.append("，".join(parts) + "。")
    if r.get("gmv_ltm_b") is not None:
        b.append(f"过去十二个月GMV为人民币{fmt_m(r['gmv_ltm_b'])}十亿元。")
    if r.get("mau_m") is not None:
        b.append(f"本季度平均月活跃用户数为{fmt_m(r['mau_m'])}百万。")
    if r.get("active_buyers_m") is not None:
        b.append(f"过去十二个月活跃买家数为{fmt_m(r['active_buyers_m'])}百万。")
    return b

def tr_title(title):
    if not title:
        return None
    return TITLE_TR.get(title.strip(), title)

def tr_speaker(sp):
    if not sp:
        return None
    return SPEAKER_TR.get(sp.strip(), sp)

def tr_quote(q):
    q = q.strip()
    return QUOTE_TR.get(q, q)  # fall back to English if not found (shouldn't happen)

out = {}
missing = []
for quarter, d in M.items():
    r = Qby.get(quarter, {})
    bullets = cn_bullets(r)
    quotes = []
    for qt in d["quotes"]:
        txt = qt["quote"]
        if is_junk(txt):
            continue
        cn = QUOTE_TR.get(txt.strip())
        if cn is None:
            missing.append((quarter, txt[:80]))
            cn = txt  # fallback
        quotes.append({
            "speaker": tr_speaker(qt["speaker"]),
            "title": tr_title(qt["title"]),
            "quote": cn,
        })
    out[quarter] = {"bullets": bullets, "quotes": quotes}

if missing:
    print(f"WARNING: {len(missing)} quotes missing translation:")
    for m in missing:
        print(" -", m)
else:
    print("All quotes translated.")

with open(os.path.join(DATA_DIR, "mgmt_cn.json"), "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=2)

print("done,", len(out), "quarters")
