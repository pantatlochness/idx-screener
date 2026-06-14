#!/usr/bin/env python3
"""
Build the LIQUID, tradable IDX universe automatically and write tickers.json.

How it stays "live":
  1. Candidate pool = bundled seed (universe_seed.json) + any codes already in
     tickers.json + best-effort live discovery from the IDX website (so brand-new
     listings get picked up when the IDX endpoint is reachable in CI).
  2. Each candidate's real liquidity is measured from Yahoo daily bars
     (avg of close*volume over the last 20 sessions).
  3. Only names trading at or above LIQ_MIN_IDR/day are kept. Illiquid or dead
     codes drop out on their own; newly-liquid names get added.

Run by .github/workflows/build-universe.yml on a weekly schedule.
Tunable via env: LIQ_MIN_IDR (default 1e9 = Rp1bn/day).
"""
import json, os, time, sys, urllib.request, urllib.error
from pathlib import Path
import fetch_data  # reuse the same Yahoo fetcher

ROOT = Path(__file__).parent
LIQ_MIN = float(os.environ.get("LIQ_MIN_IDR", "1e9"))
UA = fetch_data.UA


def load_seed():
    """sector map {code: sector} and the candidate set from the seed file."""
    raw = json.loads((ROOT / "universe_seed.json").read_text(encoding="utf-8"))
    sector_of, cands = {}, set()
    for sector, codes in raw.items():
        if sector.startswith("_"):
            continue
        for c in codes:
            sector_of[c] = sector
            cands.add(c)
    return sector_of, cands


def load_known_names():
    """Keep nice display names already present in tickers.json."""
    f = ROOT / "tickers.json"
    names = {}
    if f.exists():
        try:
            for row in json.loads(f.read_text(encoding="utf-8")):
                if len(row) >= 2 and row[1]:
                    names[row[0]] = row[1]
        except Exception:
            pass
    return names


def discover_idx():
    """Best-effort: pull all listed codes from the IDX website. Returns a set
    (empty if blocked). Never fatal -- the seed is the fallback."""
    url = ("https://www.idx.co.id/primary/StockData/GetSecuritiesStock"
           "?start=0&length=9999&code=&sector=&board=&language=en-us")
    try:
        req = urllib.request.Request(url, headers={
            "User-Agent": UA, "Accept": "application/json",
            "Referer": "https://www.idx.co.id/", "X-Requested-With": "XMLHttpRequest"})
        with urllib.request.urlopen(req, timeout=25) as r:
            j = json.load(r)
        rows = j.get("data") or j.get("Data") or []
        codes = {str(x.get("Code") or x.get("code")).upper().strip()
                 for x in rows if (x.get("Code") or x.get("code"))}
        codes = {c for c in codes if len(c) == 4 and c.isalpha()}
        print(f"IDX discovery: {len(codes)} codes")
        return codes
    except Exception as e:
        print(f"IDX discovery failed ({repr(e)[:80]}) -- using seed only", file=sys.stderr)
        return set()


def avg_value_traded(bars):
    c, v = bars["c"], bars["v"]
    n = min(20, len(c))
    if n < 10:
        return 0.0
    vals = [c[-i] * v[-i] for i in range(1, n + 1)]
    return sum(vals) / len(vals)


def main():
    sector_of, cands = load_seed()
    names = load_known_names()
    cands |= set(names.keys())          # retain anything already shipped
    cands |= discover_idx()             # add live-discovered listings
    cands = sorted(cands)
    print(f"Testing {len(cands)} candidate codes for liquidity >= Rp{LIQ_MIN:,.0f}/day")

    kept, drop, fail = [], 0, 0
    for i, code in enumerate(cands, 1):
        bars = fetch_data.fetch_one(code)
        if not bars:
            fail += 1
        else:
            avt = avg_value_traded(bars)
            if avt >= LIQ_MIN:
                kept.append([code, names.get(code, code), sector_of.get(code, "Other"), round(avt)])
            else:
                drop += 1
        if i % 25 == 0:
            print(f"  {i}/{len(cands)} ({len(kept)} liquid, {drop} illiquid, {fail} no-data)")
        time.sleep(0.25)

    # sort by sector then by liquidity desc; strip the liquidity helper column
    kept.sort(key=lambda r: (r[2], -r[3]))
    out = [[r[0], r[1], r[2]] for r in kept]
    (ROOT / "tickers.json").write_text(json.dumps(out, ensure_ascii=False, indent=0),
                                       encoding="utf-8")
    print(f"Wrote tickers.json: {len(out)} liquid names "
          f"({drop} dropped as illiquid, {fail} no data)")
    if len(out) < 30:
        sys.exit("ERROR: suspiciously few liquid names -- Yahoo may be blocking this IP.")


if __name__ == "__main__":
    main()
