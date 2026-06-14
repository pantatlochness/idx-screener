#!/usr/bin/env python3
"""
Fetch daily OHLCV bars for the IDX liquid universe from Yahoo Finance
and write data.json. The dashboard (index.html) reads this file from the
same origin, so there is no CORS problem and no client-side proxy needed.

Scoring is intentionally NOT done here -- the dashboard's JS engine computes
scores from these raw bars, so the logic lives in exactly one place.

Run locally:   python fetch_data.py
In CI:         invoked by .github/workflows/update.yml on a schedule
"""
import json, time, sys, urllib.request, urllib.error
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).parent
RANGE = "3mo"
INTERVAL = "1d"
HOSTS = ["query1.finance.yahoo.com", "query2.finance.yahoo.com"]
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")


def load_universe():
    data = json.loads((ROOT / "tickers.json").read_text(encoding="utf-8"))
    # tickers.json rows are [symbol, name, sector]; we only need the symbol here
    return [row[0] for row in data]


def fetch_one(sym, retries=2):
    path = (f"/v8/finance/chart/{sym}.JK?range={RANGE}&interval={INTERVAL}")
    last = None
    for attempt in range(retries):
        host = HOSTS[attempt % len(HOSTS)]
        url = f"https://{host}{path}"
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA,
                                                       "Accept": "application/json"})
            with urllib.request.urlopen(req, timeout=20) as r:
                j = json.load(r)
            res = j["chart"]["result"][0]
            q = res["indicators"]["quote"][0]
            o, h, l, c, v = [], [], [], [], []
            closes = q.get("close") or []
            for i in range(len(closes)):
                if closes[i] is None:
                    continue
                o.append(round(q["open"][i], 4) if q["open"][i] is not None else closes[i])
                h.append(round(q["high"][i], 4) if q["high"][i] is not None else closes[i])
                l.append(round(q["low"][i], 4) if q["low"][i] is not None else closes[i])
                c.append(round(closes[i], 4))
                v.append(int(q["volume"][i] or 0))
            if len(c) >= 20:
                return {"o": o, "h": h, "l": l, "c": c, "v": v}
            last = f"only {len(c)} bars"
        except urllib.error.HTTPError as e:
            last = f"HTTP {e.code}"
        except Exception as e:  # noqa
            last = repr(e)[:80]
        time.sleep(0.8 * (attempt + 1))
    print(f"  ! {sym}: {last}", file=sys.stderr)
    return None


def main():
    syms = load_universe()
    print(f"Fetching {len(syms)} tickers from Yahoo Finance...")
    bars, ok, fail = {}, 0, 0
    for i, sym in enumerate(syms, 1):
        b = fetch_one(sym)
        if b:
            bars[sym] = b
            ok += 1
        else:
            fail += 1
        if i % 25 == 0:
            print(f"  {i}/{len(syms)} done ({ok} ok, {fail} failed)")
        time.sleep(0.25)  # be polite to the API / avoid rate limits

    out = {
        "generatedAt": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "source": "yahoo-finance-chart",
        "range": RANGE,
        "count": ok,
        "failed": fail,
        "bars": bars,
    }
    (ROOT / "data.json").write_text(json.dumps(out, separators=(",", ":")),
                                    encoding="utf-8")
    print(f"Wrote data.json: {ok} tickers ({fail} failed) at {out['generatedAt']}")
    # Non-zero exit only if literally nothing came back, so CI can flag a total outage
    if ok == 0:
        sys.exit("ERROR: no data fetched -- Yahoo may be blocking this IP.")


if __name__ == "__main__":
    main()
