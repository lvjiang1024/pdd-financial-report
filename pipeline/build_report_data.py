import json, os

SCRATCH = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(SCRATCH, "data")
REPORTS_DIR = os.path.join(os.path.dirname(SCRATCH), "reports")

q = json.load(open(os.path.join(DATA_DIR, "quarterly_raw.json")))
a = json.load(open(os.path.join(DATA_DIR, "annual_raw.json")))
mgmt = json.load(open(os.path.join(DATA_DIR, "mgmt_cn.json")))

for r in q:
    if r["revenue"] is not None and r["cost_of_revenue"] is not None:
        r["gross_profit"] = round(r["revenue"] - r["cost_of_revenue"], 1)
    else:
        r["gross_profit"] = None

for y, r in a.items():
    if r["revenue"] is not None and r["cost_of_revenue"] is not None:
        r["gross_profit"] = round(r["revenue"] - r["cost_of_revenue"], 1)
    else:
        r["gross_profit"] = None

years_sorted = sorted(a.keys())
for y in years_sorted:
    r = a[y]
    ta, tl, ni = r.get("total_assets"), r.get("total_liabilities"), r.get("net_income")
    if ta is not None and tl is not None:
        equity = ta - tl
        r["equity"] = round(equity, 1)
        r["roe_pct"] = round(ni / equity * 100, 1) if ni is not None and equity else None
        r["roa_pct"] = round(ni / ta * 100, 1) if ni is not None and ta else None
        r["debt_ratio_pct"] = round(tl / ta * 100, 1) if ta else None
    else:
        r["equity"] = r["roe_pct"] = r["roa_pct"] = r["debt_ratio_pct"] = None

data = {
    "quarterly": q,
    "annual": [a[y] for y in years_sorted],
    "mgmt": mgmt,
}

with open(os.path.join(DATA_DIR, "final_data.json"), "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

data_json_min = json.dumps(data, ensure_ascii=False)
with open(os.path.join(DATA_DIR, "final_data_min.json"), "w", encoding="utf-8") as f:
    f.write(data_json_min)

# Assemble the final standalone HTML report
tmpl = open(os.path.join(SCRATCH, "report_template.html"), encoding="utf-8").read()
out = tmpl.replace("__DATA_JSON__", data_json_min)

os.makedirs(REPORTS_DIR, exist_ok=True)
report_path = os.path.join(REPORTS_DIR, "PDD_Holdings_财务分析报告.html")
with open(report_path, "w", encoding="utf-8") as f:
    f.write(out)

# also drop a copy of the final data JSON next to the report for reference
with open(os.path.join(REPORTS_DIR, "PDD_quarterly_data.json"), "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

# keep the GitHub Pages copy (docs/index.html) in sync, if this repo publishes via GitHub Pages
docs_dir = os.path.join(os.path.dirname(SCRATCH), "docs")
if os.path.isdir(docs_dir):
    with open(os.path.join(docs_dir, "index.html"), "w", encoding="utf-8") as f:
        f.write(out)
    print(f"docs/index.html updated (GitHub Pages)")

print(f"done: {len(q)} quarters, {len(years_sorted)} years")
print(f"report written to {report_path}")
