"""
Fetch one new PDD Holdings 6-K earnings-release exhibit from SEC EDGAR and
register it in data/quarters.json, ready for the next pipeline run.

Usage:
    python3 add_quarter.py 2026Q2 <accession-number>

Find the accession number by checking the latest filings at:
    https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=0001737806&type=6-K&dateb=&owner=include&count=10
or ask Claude to look it up on SEC EDGAR (CIK 0001737806) directly.
"""
import sys, os, re, json, subprocess

SCRATCH = os.path.dirname(os.path.abspath(__file__))
RAW_DIR = os.path.join(SCRATCH, "raw_filings")
DATA_DIR = os.path.join(SCRATCH, "data")
UA = "research contact@example.com"


def find_ex99_url(accession):
    acc_nodash = accession.replace("-", "")
    dir_url = f"https://www.sec.gov/Archives/edgar/data/1737806/{acc_nodash}/"
    r = subprocess.run(["curl", "-s", "-A", UA, "--max-time", "20", dir_url],
                        capture_output=True, text=True)
    hrefs = re.findall(r'href="([^"]+)"', r.stdout)
    ex_hrefs = [h for h in hrefs if "ex99" in h.lower() and h.endswith(".htm")]
    if not ex_hrefs:
        return None
    h = ex_hrefs[0]
    return "https://www.sec.gov" + h if h.startswith("/") else h


def main():
    if len(sys.argv) != 3:
        print(__doc__)
        sys.exit(1)
    quarter, accession = sys.argv[1], sys.argv[2]

    ex_url = find_ex99_url(accession)
    if not ex_url:
        print(f"Could not find an EX-99 exhibit for accession {accession}")
        sys.exit(1)

    out_path = os.path.join(RAW_DIR, accession + ".htm")
    subprocess.run(["curl", "-s", "-A", UA, "--max-time", "20", ex_url, "-o", out_path])
    size = os.path.getsize(out_path) if os.path.exists(out_path) else 0
    if size < 50000:
        print(f"WARNING: downloaded file is only {size} bytes — likely not the earnings release. Check {ex_url} manually.")
    else:
        print(f"Downloaded {ex_url} -> {out_path} ({size} bytes)")

    qmap_path = os.path.join(DATA_DIR, "quarters.json")
    qmap = json.load(open(qmap_path))
    qmap[quarter] = accession
    # keep chronological-ish order by re-sorting on insertion (dict preserves insertion order in py3.7+,
    # but sort by year+quarter to be safe since new quarters may be added out of order)
    def sort_key(k):
        y, q = k[:4], k[5:]
        return (int(y), int(q))
    qmap = {k: qmap[k] for k in sorted(qmap, key=sort_key)}
    json.dump(qmap, open(qmap_path, "w"), indent=2)
    print(f"Registered {quarter} -> {accession} in {qmap_path}")
    print("\nNext: run the pipeline to rebuild the report:")
    print("  cd pipeline && python3 extract.py && python3 extract_mgmt.py && python3 build_mgmt_cn.py && python3 build_report_data.py")


if __name__ == "__main__":
    main()
