import re, html as htmlmod, json, os

SCRATCH = os.path.dirname(os.path.abspath(__file__))
RAW_DIR = os.path.join(SCRATCH, "raw_filings")
DATA_DIR = os.path.join(SCRATCH, "data")

with open(os.path.join(DATA_DIR, "quarters.json")) as f:
    Q_MAP = json.load(f)

def load_text(acc):
    path = os.path.join(RAW_DIR, acc + ".htm")
    h = open(path, encoding="utf-8", errors="ignore").read()
    t = re.sub(r"<[^>]+>", " ", h)
    t = htmlmod.unescape(t)
    t = re.sub(r"\s+", " ", t)
    # fix footnote-superscript artifacts that split words with a stray space
    t = t.replace("a ttributable", "attributable")
    return t

def to_million(value_str, unit):
    v = float(value_str.replace(",", ""))
    if unit and unit.lower().startswith("b"):
        v *= 1000.0
    return v

AMT = r"RMB\s?\(?([\d,\.]+)\)?\s*(million|billion)"

def find_amount(pattern, text, flags=re.IGNORECASE):
    """pattern must contain one group for number handled via AMT embedded, returns (value_in_million, matched_text) or (None, None)."""
    m = re.search(pattern, text, flags)
    if not m:
        return None, None
    return to_million(m.group("num"), m.group("unit")), m.group(0)

def extract_quarter(quarter, text):
    row = {"quarter": quarter}

    def amt(label_pattern):
        pat = label_pattern + r"\s*RMB\s?\(?(?P<num>[\d,\.]+)\)?\s*(?P<unit>million|billion)"
        val, matched = find_amount(pat, text)
        return val

    def amt_signed(label_pattern):
        pat = label_pattern + r"\s*RMB\s?\(?(?P<num>[\d,\.]+)\)?\s*(?P<unit>million|billion)"
        m = re.search(pat, text, re.IGNORECASE)
        if not m:
            return None
        val = to_million(m.group("num"), m.group("unit"))
        return -val if "loss" in m.group(0).lower() else val

    row["revenue"] = amt(r"Total revenues? (?:in the quarter )?were")
    row["rev_marketing"] = amt(r"Revenues from online marketing services(?: and others)? were")
    row["rev_transaction"] = amt(r"Revenues from transaction services were")
    row["rev_merchandise"] = amt(r"Revenues from merchandise sales were")

    row["cost_of_revenue"] = amt(r"Total costs of revenues? were")
    row["opex_total"] = amt(r"Total operating expenses were")
    row["sm_expense"] = amt(r"Sales and marketing expenses were")
    row["ga_expense"] = amt(r"General and administrative expenses (?:were|was)")
    row["rd_expense"] = amt(r"Research and development expenses were")

    row["operating_profit"] = amt_signed(r"Operating (?:profit|loss) (?:in the quarter )?was")
    row["nongaap_operating_profit"] = amt_signed(r"Non-GAAP operating (?:profit|loss) (?:in the quarter )?was")
    row["net_income"] = amt_signed(r"Net (?:income|loss) attributable to ordinary shareholders (?:in the quarter )?was")
    row["nongaap_net_income"] = amt_signed(r"Non-GAAP net (?:income|loss) attributable to ordinary shareholders (?:in the quarter )?was")

    # EPS - separate basic/diluted phrasing (profit quarters)
    m = re.search(r"Basic earnings per ADS was RMB\(?([\d,\.]+)\)?", text, re.IGNORECASE)
    row["eps_basic_ads"] = float(m.group(1)) if m else None
    m = re.search(r"diluted earnings per ADS was RMB\(?([\d,\.]+)\)?", text, re.IGNORECASE)
    row["eps_diluted_ads"] = float(m.group(1)) if m else None
    m = re.search(r"Non-GAAP diluted earnings per ADS\s+was RMB\(?([\d,\.]+)\)?", text, re.IGNORECASE)
    row["nongaap_eps_diluted_ads"] = float(m.group(1)) if m else None

    # EPS - combined "Basic and diluted net loss per ADS was RMBx.xx" phrasing (loss quarters)
    if row["eps_basic_ads"] is None:
        m = re.search(r"Basic and diluted net loss per ADS was RMB\(?([\d,\.]+)\)?", text, re.IGNORECASE)
        if m:
            row["eps_basic_ads"] = -float(m.group(1))
            row["eps_diluted_ads"] = -float(m.group(1))
    if row["nongaap_eps_diluted_ads"] is None:
        m = re.search(r"Non-GAAP basic and diluted net loss per ADS (?:were|was) RMB\(?([\d,\.]+)\)?", text, re.IGNORECASE)
        if m:
            row["nongaap_eps_diluted_ads"] = -float(m.group(1))

    row["ocf"] = amt(r"Net cash generated from operating activities was")

    m = re.search(r"Cash,\s*cash equivalents and short-term investments were RMB([\d,\.]+) billion", text, re.IGNORECASE)
    row["cash_position_b"] = float(m.group(1).replace(",", "")) if m else None

    bs_divisor = 1000.0
    bsm = re.search(r"BALANCE SHEETS.{0,80}Amounts in (thousands|millions) of Renminbi", text, re.IGNORECASE)
    if bsm and bsm.group(1).lower() == "millions":
        bs_divisor = 1.0
    m = re.search(r"Total assets\s+[\d,]+\s+([\d,]+)", text, re.IGNORECASE)
    row["total_assets"] = float(m.group(1).replace(",", "")) / bs_divisor if m else None
    m = re.search(r"Total liabilities\s+[\d,]+\s+([\d,]+)", text, re.IGNORECASE)
    row["total_liabilities"] = float(m.group(1).replace(",", "")) / bs_divisor if m else None

    m = re.search(r"GMV\D{0,15}(?:in the twelve-month period[^)]*\))? was RMB([\d,\.]+) billion", text, re.IGNORECASE)
    row["gmv_ltm_b"] = float(m.group(1).replace(",", "")) if m else None
    m = re.search(r"Average monthly active users\D{0,15}in the quarter were ([\d,\.]+) million", text, re.IGNORECASE)
    row["mau_m"] = float(m.group(1).replace(",", "")) if m else None
    m = re.search(r"Active buyers\D{0,40}were ([\d,\.]+) million", text, re.IGNORECASE)
    row["active_buyers_m"] = float(m.group(1).replace(",", "")) if m else None

    return row


def extract_annual(quarter, text):
    first = text.find("Fiscal Year")
    if first < 0:
        return None
    idx = text.find("Fiscal Year", first + 1)
    if idx < 0:
        idx = first
    fy_text = text[idx: idx + 6000]
    year = quarter[:4]
    row = {"year": year}

    def amt(label_pattern, src=fy_text):
        pat = label_pattern + r"\s*RMB\s?\(?(?P<num>[\d,\.]+)\)?\s*(?P<unit>million|billion)"
        m = re.search(pat, src, re.IGNORECASE)
        if not m:
            return None
        return to_million(m.group("num"), m.group("unit"))

    def amt_signed(label_pattern, src=fy_text):
        pat = label_pattern + r"\s*RMB\s?\(?(?P<num>[\d,\.]+)\)?\s*(?P<unit>million|billion)"
        m = re.search(pat, src, re.IGNORECASE)
        if not m:
            return None
        val = to_million(m.group("num"), m.group("unit"))
        return -val if "loss" in m.group(0).lower() else val

    row["revenue"] = amt(r"Total revenues? were")
    row["rev_marketing"] = amt(r"Revenues from online marketing services(?: and others)? were")
    row["rev_transaction"] = amt(r"Revenues from transaction services were")
    row["rev_merchandise"] = amt(r"Revenues from merchandise sales were")
    row["cost_of_revenue"] = amt(r"Total costs of revenues? were")
    row["sm_expense"] = amt(r"Sales and marketing expenses were")
    row["ga_expense"] = amt(r"General and administrative expenses (?:were|was)")
    row["rd_expense"] = amt(r"Research and development expenses were")

    row["operating_profit"] = amt_signed(r"Operating (?:profit|loss) was")
    row["nongaap_operating_profit"] = amt_signed(r"Non-GAAP operating (?:profit|loss) was")
    row["net_income"] = amt_signed(r"Net (?:income|loss) attributable to ordinary shareholders was")
    row["nongaap_net_income"] = amt_signed(r"Non-GAAP net (?:income|loss) attributable to ordinary shareholders was")
    row["ocf"] = amt(r"Net cash generated from operating activities was")

    m = re.search(r"Basic earnings per ADS was RMB\(?([\d,\.]+)\)?", fy_text, re.IGNORECASE)
    row["eps_basic_ads"] = float(m.group(1)) if m else None
    m = re.search(r"diluted earnings per ADS was RMB\(?([\d,\.]+)\)?", fy_text, re.IGNORECASE)
    row["eps_diluted_ads"] = float(m.group(1)) if m else None
    m = re.search(r"Non-GAAP diluted earnings per ADS\s+was RMB\(?([\d,\.]+)\)?", fy_text, re.IGNORECASE)
    row["nongaap_eps_diluted_ads"] = float(m.group(1)) if m else None
    if row["eps_basic_ads"] is None:
        m = re.search(r"Basic and diluted net loss per ADS was RMB\(?([\d,\.]+)\)?", fy_text, re.IGNORECASE)
        if m:
            row["eps_basic_ads"] = -float(m.group(1))
            row["eps_diluted_ads"] = -float(m.group(1))

    bs_divisor = 1000.0
    bsm = re.search(r"BALANCE SHEETS.{0,80}Amounts in (thousands|millions) of Renminbi", text, re.IGNORECASE)
    if bsm and bsm.group(1).lower() == "millions":
        bs_divisor = 1.0
    m = re.search(r"Total assets\s+[\d,]+\s+([\d,]+)", text, re.IGNORECASE)
    row["total_assets"] = float(m.group(1).replace(",", "")) / bs_divisor if m else None
    m = re.search(r"Total liabilities\s+[\d,]+\s+([\d,]+)", text, re.IGNORECASE)
    row["total_liabilities"] = float(m.group(1).replace(",", "")) / bs_divisor if m else None

    return row


def extract_mgmt_section(text):
    hidx = text.find("Highlights")
    end_idx = text.find("Conference Call")
    if end_idx < 0:
        end_idx = hidx + 4000
    return text[hidx:end_idx][:5000] if hidx >= 0 else text[:3000]


def main():
    quarterly = []
    annual = {}
    mgmt_raw = {}
    for q, acc in Q_MAP.items():
        text = load_text(acc)
        row = extract_quarter(q, text)
        quarterly.append(row)
        if "Q4" in q:
            fy = extract_annual(q, text)
            if fy:
                annual[fy["year"]] = fy
        mgmt_raw[q] = extract_mgmt_section(text)

    with open(os.path.join(DATA_DIR, "quarterly_raw.json"), "w") as f:
        json.dump(quarterly, f, ensure_ascii=False, indent=2)
    with open(os.path.join(DATA_DIR, "annual_raw.json"), "w") as f:
        json.dump(annual, f, ensure_ascii=False, indent=2)
    with open(os.path.join(DATA_DIR, "mgmt_raw.json"), "w") as f:
        json.dump(mgmt_raw, f, ensure_ascii=False, indent=2)

    print("Quarters extracted:", len(quarterly))
    print("Years extracted:", list(annual.keys()))

if __name__ == "__main__":
    main()
