import re, json, os

SCRATCH = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(SCRATCH, "data")
mgmt_raw = json.load(open(os.path.join(DATA_DIR, "mgmt_raw.json")))

def clean(s):
    s = s.replace("’", "'").replace("‘", "'")
    s = re.sub(r"\s+", " ", s).strip()
    return s

def extract_quotes(text):
    quotes = []
    for m in re.finditer(r"“([^”]{20,600})”", text):
        quote = clean(m.group(1))
        tail = text[m.end(): m.end() + 200]
        sm = re.search(r"(?:said|added,?)\s+(Mr\.|Ms\.|Mrs\.)\s*([A-Za-z\-\. ]+?),\s*([^.“]+)\.", tail)
        if sm:
            speaker = f"{sm.group(1)} {sm.group(2).strip()}"
            title = clean(sm.group(3))
        else:
            speaker, title = None, None
        quotes.append({"speaker": speaker, "title": title, "quote": quote})
    # merge quotes with same speaker consecutively (multi-paragraph quotes) -- keep separate but tag
    return quotes

def extract_highlights_bullets(text):
    # bullets are delimited by "·" in flattened text
    parts = text.split("·")
    bullets = []
    for p in parts[1:6]:  # first ~5 bullets under "Highlights"
        p = clean(p)
        # cut at first "1 This announcement" / footnote junk or overly long
        p = re.split(r"\s\d\s(?:This announcement|The Company)", p)[0]
        if len(p) > 400:
            p = p[:400]
        if len(p) > 15:
            bullets.append(p)
    return bullets

out = {}
for q, text in mgmt_raw.items():
    quotes = extract_quotes(text)
    bullets = extract_highlights_bullets(text)
    out[q] = {"bullets": bullets, "quotes": quotes}

with open(os.path.join(DATA_DIR, "mgmt_structured.json"), "w") as f:
    json.dump(out, f, ensure_ascii=False, indent=2)

# print a sample for review
for q in ["2018Q2", "2021Q1", "2023Q4", "2024Q4", "2026Q1"]:
    print("=====", q, "=====")
    print("BULLETS:")
    for b in out[q]["bullets"]:
        print(" -", b[:200])
    print("QUOTES:")
    for qq in out[q]["quotes"]:
        print(" -", qq["speaker"], "|", qq["title"], "|", qq["quote"][:150])
    print()
