#!/usr/bin/env python3
"""
Backtester for the IDX screener's scoring logic.

It re-implements the dashboard's engine (Daily / Swing / Scalp profiles, the
accumulation layer, the chase guard, and the ATR risk levels) in Python and runs
it over multi-year Yahoo .JK history to answer one question with evidence:

    Does a higher score actually lead to better forward returns, and what is the
    real win rate / expectancy of each setup?

Two independent studies are produced:
  1. SIGNAL-QUALITY (forward-return) study - no stops/targets, no path assumptions.
     For every (day, ticker) it records the score and the H-day forward return,
     then buckets by score. If the score is meaningful, average forward return
     should rise with the score bucket. This is the cleanest test of the edge.
  2. TRADE SIMULATION - realistic: enter next day's OPEN when score>=threshold,
     exit on ATR stop / target / time-stop, deduct round-trip costs. Reports win
     rate, average win/loss, expectancy (in R), profit factor, max drawdown,
     broken down by profile, by setup, and by year, vs a buy&hold benchmark.

NO LOOKAHEAD: every signal at day t uses only bars[0..t]; entries fill at t+1.

Honest limits (also printed in the report):
  - Survivorship bias: the universe is today's liquid names, so history is biased
    toward winners. Treat absolute returns as optimistic; trust the *relative*
    signal (higher score vs lower) more than the headline number.
  - Scalp on daily bars approximates buy-open/sell-close; it cannot model real
    intraday timing or bid/ask.
  - Costs/slippage are modelled with a flat round-trip assumption.

Run:  python backtest.py            (env: BT_YEARS, BT_ENTRY_SCORE, BT_COST)
"""
import os, sys, json, time, math, urllib.request, urllib.error
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).parent
YEARS = os.environ.get("BT_YEARS", "3y")          # 1y/2y/3y/5y/max
ENTRY_SCORE = float(os.environ.get("BT_ENTRY_SCORE", "65"))
COST = float(os.environ.get("BT_COST", "0.003"))  # round-trip cost+slippage (0.3%)
MIN_VALUE_BN = float(os.environ.get("BT_MIN_VALUE_BN", "1.0"))  # liquidity gate (Rp bn/day)
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")
HOSTS = ["query1.finance.yahoo.com", "query2.finance.yahoo.com"]

PROFILES = ["daily", "swing", "scalp"]
HORIZON = {"daily": 5, "swing": 10, "scalp": 1}      # forward-return window (signal-quality study)
# --- REWORKED EXITS: trade with the trend, wide disaster stop + MA trailing exit ---
MAXHOLD  = {"daily": 20, "swing": 45, "scalp": 1}    # generous safety cap; the trail usually fires first
TRAILMA  = {"daily": 10, "swing": 20, "scalp": 1}    # exit on a daily CLOSE below this MA (trend break)
DISASTER = {"daily": 3.0, "swing": 3.5, "scalp": 1.0}# catastrophe stop in xATR (wide, to avoid noise whipsaw)
RISK = {"daily": (1.5, 3.0), "swing": (2.0, 5.0), "scalp": (0.8, 1.5)}  # legacy levels for analyze() display only
# setups proven to lose / not worth trading -> never entered in the simulation
NON_TRADABLE = {"Oversold Bounce", "Avoid – Downtrend", "Avoid – Too thin/quiet",
                "Neutral / No setup", "Watch", "Overbought – caution"}

# ------------------------------------------------------------------ data
def fetch_history(sym, rng=YEARS, retries=3, suffix=".JK"):
    path = f"/v8/finance/chart/{sym}{suffix}?range={rng}&interval=1d"
    for attempt in range(retries):
        host = HOSTS[attempt % len(HOSTS)]
        try:
            req = urllib.request.Request(f"https://{host}{path}",
                                         headers={"User-Agent": UA, "Accept": "application/json"})
            with urllib.request.urlopen(req, timeout=30) as r:
                j = json.load(r)
            res = j["chart"]["result"][0]; q = res["indicators"]["quote"][0]
            o, h, l, c, v = [], [], [], [], []
            cl = q.get("close") or []
            for i in range(len(cl)):
                if cl[i] is None:
                    continue
                o.append(q["open"][i] if q["open"][i] is not None else cl[i])
                h.append(q["high"][i] if q["high"][i] is not None else cl[i])
                l.append(q["low"][i] if q["low"][i] is not None else cl[i])
                c.append(cl[i]); v.append(q["volume"][i] or 0)
            ts = res.get("timestamp") or list(range(len(c)))
            if len(c) >= 120:
                return {"o": o, "h": h, "l": l, "c": c, "v": v, "t": ts[-len(c):]}
        except Exception:
            time.sleep(1.0 * (attempt + 1))
    return None

# ------------------------------------------------------------------ indicators
def sma(a, n):
    if len(a) < n: return None
    return sum(a[-n:]) / n

def ema_last(a, n):
    if len(a) < n: return None
    k = 2 / (n + 1); e = sum(a[:n]) / n
    for i in range(n, len(a)): e = a[i] * k + e * (1 - k)
    return e

def ema_series(a, n):
    if len(a) < n: return []
    k = 2 / (n + 1); out = [None] * len(a); e = sum(a[:n]) / n; out[n - 1] = e
    for i in range(n, len(a)): e = a[i] * k + e * (1 - k); out[i] = e
    return out

def rsi(c, n=14):
    if len(c) < n + 1: return None
    g = l = 0.0
    for i in range(1, n + 1):
        d = c[i] - c[i - 1]
        if d >= 0: g += d
        else: l -= d
    g /= n; l /= n
    for i in range(n + 1, len(c)):
        d = c[i] - c[i - 1]
        g = (g * (n - 1) + (d if d > 0 else 0)) / n
        l = (l * (n - 1) + (-d if d < 0 else 0)) / n
    if l == 0: return 100.0
    return 100 - 100 / (1 + g / l)

def macd(c):
    f, s = ema_series(c, 12), ema_series(c, 26)
    if not any(x is not None for x in s): return None
    line = [ (f[i] - s[i]) if (f[i] is not None and s[i] is not None) else None for i in range(len(c)) ]
    ml = [x for x in line if x is not None]
    sig = ema_last(ml, 9); m = line[-1]
    if m is None or sig is None: return None
    return {"macd": m, "signal": sig, "hist": m - sig}

def atr(h, l, c, n=14):
    if len(c) < n + 1: return None
    tr = [max(h[i] - l[i], abs(h[i] - c[i - 1]), abs(l[i] - c[i - 1])) for i in range(1, len(c))]
    a = sum(tr[:n]) / n
    for i in range(n, len(tr)): a = (a * (n - 1) + tr[i]) / n
    return a

def accumulation(o, h, l, c, v):
    n = len(c)
    obv = [0.0]
    for i in range(1, n):
        obv.append(obv[i - 1] + (v[i] if c[i] > c[i - 1] else -v[i] if c[i] < c[i - 1] else 0))
    obv_up = (obv[-1] - obv[-11]) > 0 if n > 11 else False
    mfv = vs = 0.0
    for i in range(max(0, n - 20), n):
        rng = (h[i] - l[i]) or 1e-9
        mfv += (((c[i] - l[i]) - (h[i] - c[i])) / rng) * v[i]; vs += v[i]
    cmf = mfv / vs if vs else 0.0
    pos = neg = 0.0
    for i in range(max(1, n - 14), n):
        tp = (h[i] + l[i] + c[i]) / 3; ptp = (h[i - 1] + l[i - 1] + c[i - 1]) / 3; mf = tp * v[i]
        if tp > ptp: pos += mf
        elif tp < ptp: neg += mf
    mfi = 100.0 if neg == 0 else 100 - 100 / (1 + pos / neg)
    uv = dv = 0.0
    for i in range(max(1, n - 20), n):
        if c[i] > c[i - 1]: uv += v[i]
        elif c[i] < c[i - 1]: dv += v[i]
    udr = uv / dv if dv else (3 if uv > 0 else 1)
    a = 50
    a += 12 if obv_up else -12
    a += 12 if cmf > 0.05 else 5 if cmf > 0 else -12 if cmf < -0.05 else -5
    a += 10 if mfi >= 55 else 3 if mfi >= 45 else -10 if mfi < 35 else -3
    a += 10 if udr >= 1.5 else 3 if udr >= 1 else -10 if udr < 0.7 else -3
    return max(0, min(100, round(a)))

def clamp(s): return max(0, min(100, round(s)))

# ------------------------------------------------------------------ scoring (mirror of index.html)
def analyze(bars, profile, chase_guard=True):
    o, h, l, c, v = bars["o"], bars["h"], bars["l"], bars["c"], bars["v"]
    n = len(c)
    if n < 30: return None
    close, prev, opn = c[-1], c[-2], o[-1]
    chg = (close - prev) / prev * 100
    ma5, ma20, ma50 = sma(c, 5), sma(c, 20), sma(c, 50) or sma(c, min(50, n - 1))
    avgv20 = sma(v, 20); volr = v[-1] / avgv20 if avgv20 else 1
    valbn = close * v[-1] / 1e9
    rsiV = rsi(c, 14); m = macd(c); a = atr(h, l, c, 14) or close * 0.03
    hi20 = max(c[max(0, n - 21):n - 1]);
    roc5 = (close - c[-6]) / c[-6] * 100 if n > 6 else 0
    roc20 = (close - c[-21]) / c[-21] * 100 if n > 21 else 0
    ma20prev = sma(c[:n - 5], 20) if n >= 25 else ma20
    ma20slope = bool(ma20 and ma20prev and ma20 > ma20prev)
    atrpct = a / close * 100
    rng10 = [ (h[i] - l[i]) / c[i] * 100 for i in range(max(1, n - 10), n) ]
    avgrange = sum(rng10) / len(rng10) if rng10 else atrpct
    dayrng = (h[-1] - l[-1]) or 1e-9
    closepos = (close - l[-1]) / dayrng
    hi3, lo3 = max(c), min(c)
    rangepos = (close - lo3) / (hi3 - lo3) if hi3 > lo3 else 0.5
    nearhigh = close >= hi20 * 0.985
    above = (1 if ma5 and close > ma5 else 0) + (1 if ma20 and close > ma20 else 0) + (1 if ma50 and close > ma50 else 0)
    stacked = bool(ma5 and ma20 and ma50 and ma5 > ma20 > ma50)
    uptrend = bool(ma50 and close > ma50 and ma20 and close > ma20 and ma5 > ma20)
    dntrend = bool(ma50 and close < ma50)
    breakout = close >= hi20

    s = 0; setup = "Neutral / No setup"
    if profile == "daily":
        mom = 0
        if breakout: mom += 14
        if roc5 > 0: mom += min(10, roc5 * 1.2)
        mom += min(6, above * 2); s += min(30, mom)
        s += 20 if volr >= 3 else 15 if volr >= 2 else 9 if volr >= 1.4 else 4 if volr >= 1 else 0
        tr = (12 if stacked else 0) + (8 if (ma20 and close > ma20) else 0); s += min(20, tr)
        if rsiV is not None:
            s += 10 if 50 <= rsiV <= 68 else 5 if 68 < rsiV <= 80 else 0 if rsiV > 80 else 6 if 40 <= rsiV < 50 else 4 if rsiV < 30 else 0
        if m: s += 10 if (m["hist"] > 0 and m["macd"] > m["signal"]) else 5 if m["hist"] > 0 else 0
        bull = False  # candlestick omitted in backtest (minor weight, last-bar only)
        if chg > 3: s += 3
        if rsiV is not None and rsiV > 80: setup = "Overbought – caution"
        elif breakout and volr >= 1.5 and above >= 2: setup = "Momentum Breakout"
        elif nearhigh and volr >= 1.4 and above >= 2: setup = "Breakout Watch"
        elif uptrend and rsiV is not None and 42 <= rsiV < 58 and close <= ma20 * 1.06 and close >= ma20 * 0.94: setup = "Pullback Buy"
        elif dntrend and volr >= 1.5 and chg >= 3: setup = "Oversold Bounce"
        elif dntrend and rsiV is not None and rsiV < 40 and chg > 0: setup = "Reversal Watch"
        elif uptrend: setup = "Trend Continuation"
    elif profile == "swing":
        t = (12 if stacked else 0) + (8 if (ma50 and close > ma50) else 0) + (10 if ma20slope else 0); s += min(30, t)
        mo = (min(15, roc20 * 0.6) if roc20 > 0 else 0) + (10 if 0.4 <= rangepos <= 0.9 else 4 if rangepos > 0.9 else 0); s += min(25, mo)
        if rsiV is not None:
            if uptrend and 40 <= rsiV <= 58: s += 20
            elif 58 < rsiV <= 68: s += 12
            elif 68 < rsiV <= 78: s += 5
            elif rsiV > 78: s += 0
            elif rsiV < 40 and uptrend: s += 8
            else: s += 4
        if m: s += 15 if (m["hist"] > 0 and m["macd"] > m["signal"]) else 8 if m["hist"] > 0 else 0
        s += 10 if volr >= 1.2 else 6 if volr >= 0.8 else 3
        if dntrend: setup = "Avoid – Downtrend"
        elif uptrend and ma20slope and rsiV is not None and 40 <= rsiV <= 58 and close <= ma20 * 1.07: setup = "Swing Buy – Pullback"
        elif (breakout or nearhigh) and uptrend and volr >= 1.2: setup = "Swing Buy – Breakout"
        elif uptrend and rsiV is not None and rsiV > 78: setup = "Uptrend – Extended"
        elif uptrend: setup = "Uptrend – Hold"
        elif rangepos < 0.4 and atrpct < 3 and m and m["hist"] > 0: setup = "Base / Accumulation"
    else:  # scalp
        li = 25 if valbn >= 50 else 18 if valbn >= 20 else 12 if valbn >= 10 else 6 if valbn >= 5 else 0; s += li
        s += 25 if avgrange >= 5 else 18 if avgrange >= 3.5 else 12 if avgrange >= 2.5 else 6 if avgrange >= 1.5 else 2
        p = (15 if volr >= 2 else 10 if volr >= 1.5 else 5 if volr >= 1 else 0) + (10 if closepos >= 0.7 else 5 if closepos >= 0.5 else 0); s += min(25, p)
        mo = (min(10, chg * 1.5) if chg > 0 else 0) + (min(5, roc5) if roc5 > 0 else 0); s += min(15, mo)
        if rsiV is not None: s += 10 if 45 <= rsiV <= 72 else 0 if rsiV > 85 else 4
        liquid = valbn >= 10; movey = avgrange >= 2.5
        if (not liquid) or avgrange < 1.5: setup = "Avoid – Too thin/quiet"
        elif liquid and movey and volr >= 1.5 and closepos >= 0.6 and chg > 0: setup = "Scalp – Momentum"
        elif liquid and movey: setup = "Scalp – Volatile mover"
        else: setup = "Watch"

    s = clamp(s)
    acc = accumulation(o, h, l, c, v)
    accw = 15 if profile == "swing" else 6 if profile == "scalp" else 12
    if acc >= 66: s = clamp(s + accw)
    elif acc < 45: s = clamp(s - round(accw * 0.7))
    if chase_guard and chg > 10:
        f = 0.5 if profile == "scalp" else 0.8
        s = clamp(s - min(20, round((chg - 10) * f)))

    stopx, tgtx = RISK[profile]
    swinglow = min(l[max(0, n - (1 if profile == "scalp" else 10 if profile == "swing" else 5)):])
    stop = max(swinglow, close - stopx * a)
    return {"score": s, "setup": setup, "close": close, "ma50": ma50, "valbn": valbn,
            "stop": stop, "target": close + tgtx * a, "chg": chg, "acc": acc, "atr": a}

# ------------------------------------------------------------------ simulation
def year_of(ts):
    try: return datetime.fromtimestamp(ts, tz=timezone.utc).year
    except Exception: return 0

def datestr(ts):
    try: return datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%Y%m%d")
    except Exception: return ""

def build_regime(idx):
    """date(YYYYMMDD) -> True if IHSG closed above its 50-day MA that day (risk-on)."""
    if not idx: return {}
    c, t = idx["c"], idx["t"]; reg = {}
    for i in range(len(c)):
        if i < 50: continue
        ma = sum(c[i - 49:i + 1]) / 50
        reg[datestr(t[i])] = c[i] > ma
    return reg

def backtest_ticker(bars, profile, regime):
    """Returns (forward_records, trades) for one ticker/profile, no lookahead.
    Entry: next open when score>=threshold, setup is tradable, and IHSG is risk-on.
    Exit: wide disaster stop (xATR) OR a daily close below the trail MA OR a time cap."""
    o, h, l, c, v, t = bars["o"], bars["h"], bars["l"], bars["c"], bars["v"], bars["t"]
    n = len(c); H = HORIZON[profile]; maxhold = MAXHOLD[profile]; trailn = TRAILMA[profile]
    fwd = []; trades = []
    in_pos = False; entry = dstop = 0.0; ebar = 0; esetup = ""; escore = 0
    for ti in range(60, n - 1):
        window = {"o": o[:ti + 1], "h": h[:ti + 1], "l": l[:ti + 1], "c": c[:ti + 1], "v": v[:ti + 1]}
        a = analyze(window, profile)
        if a is None: continue
        liquid = a["valbn"] >= MIN_VALUE_BN
        # signal-quality forward study (pure hold, no exits/regime)
        if ti + H < n and liquid:
            fwd.append((a["score"], (c[ti + H] - c[ti]) / c[ti] * 100))
        # realistic trade simulation
        if not in_pos:
            risk_on = regime.get(datestr(t[ti]), True)
            if (liquid and a["score"] >= ENTRY_SCORE and a["setup"] not in NON_TRADABLE
                    and risk_on and ti + 1 < n):
                in_pos = True; entry = o[ti + 1]; dstop = entry - DISASTER[profile] * a["atr"]
                ebar = ti + 1; esetup = a["setup"]; escore = a["score"]
        else:
            d = ti
            trail = sma(c[:d + 1], trailn)
            ex = None
            if o[d] <= dstop: ex = o[d]                                   # gap through disaster stop
            elif l[d] <= dstop: ex = dstop
            elif trail is not None and d > ebar and c[d] < trail: ex = c[d]  # trend break (MA trail)
            elif (d - ebar) >= maxhold: ex = c[d]                         # safety time cap
            if ex is not None:
                risk = (entry - dstop) / entry if entry > dstop else 0.01
                ret = (ex - entry) / entry - COST
                trades.append({"ret": ret * 100, "R": max(-5.0, min(10.0, ret / risk)) if risk > 0 else 0,
                               "win": ret > 0, "hold": d - ebar, "setup": esetup,
                               "score": escore, "year": year_of(t[ebar]) if ebar < len(t) else 0})
                in_pos = False
    return fwd, trades

# ------------------------------------------------------------------ stats
def stat_block(trades):
    if not trades: return None
    n = len(trades); wins = [x for x in trades if x["win"]]; losses = [x for x in trades if not x["win"]]
    awin = sum(x["ret"] for x in wins) / len(wins) if wins else 0
    alos = sum(x["ret"] for x in losses) / len(losses) if losses else 0
    gp = sum(x["ret"] for x in wins); gl = -sum(x["ret"] for x in losses)
    eq = 0; peak = 0; mdd = 0
    for x in trades:
        eq += x["ret"]; peak = max(peak, eq); mdd = min(mdd, eq - peak)
    return {"n": n, "winrate": len(wins) / n * 100, "avg_win": awin, "avg_loss": alos,
            "expectancy": sum(x["ret"] for x in trades) / n, "avg_R": sum(x["R"] for x in trades) / n,
            "profit_factor": (gp / gl) if gl > 0 else float("inf"), "avg_hold": sum(x["hold"] for x in trades) / n,
            "max_dd": mdd, "total": eq}

def buckets(fwd):
    bks = [(0, 50), (50, 60), (60, 70), (70, 80), (80, 101)]
    out = []
    for lo, hi in bks:
        sub = [r for sc, r in fwd if lo <= sc < hi]
        if sub:
            out.append((f"{lo}-{hi-1 if hi<101 else 100}", len(sub), sum(sub) / len(sub),
                        sum(1 for r in sub if r > 0) / len(sub) * 100))
    return out

# ------------------------------------------------------------------ main
def main():
    syms = [row[0] for row in json.loads((ROOT / "tickers.json").read_text(encoding="utf-8"))]
    print(f"Backtesting {len(syms)} tickers over {YEARS} | entry score>={ENTRY_SCORE} | cost {COST*100:.1f}% round-trip")
    data = {}
    for i, s in enumerate(syms, 1):
        b = fetch_history(s)
        if b: data[s] = b
        if i % 25 == 0: print(f"  fetched {i}/{len(syms)} ({len(data)} ok)")
        time.sleep(0.25)
    print(f"History fetched for {len(data)} tickers")
    if len(data) < 20: sys.exit("ERROR: too little data (Yahoo may be blocking this IP).")

    idx = fetch_history("^JKSE", suffix="")           # IHSG composite for the regime filter
    regime = build_regime(idx)
    if regime:
        ron = sum(1 for x in regime.values() if x)
        print(f"Regime (IHSG vs MA50): {ron}/{len(regime)} days risk-on")
    else:
        print("Regime: IHSG unavailable -- entries not regime-gated")

    report = {"generatedAt": datetime.now(timezone.utc).isoformat(timespec="seconds"),
              "years": YEARS, "entryScore": ENTRY_SCORE, "cost": COST, "tickers": len(data),
              "regimeGated": bool(regime), "profiles": {}}
    for prof in PROFILES:
        all_fwd, all_trades = [], []
        for s, b in data.items():
            fwd, tr = backtest_ticker(b, prof, regime)
            all_fwd += fwd; all_trades += tr
        overall = stat_block(all_trades)
        by_setup = {}
        for setup in sorted(set(x["setup"] for x in all_trades)):
            by_setup[setup] = stat_block([x for x in all_trades if x["setup"] == setup])
        by_year = {}
        for yr in sorted(set(x["year"] for x in all_trades)):
            by_year[str(yr)] = stat_block([x for x in all_trades if x["year"] == yr])
        report["profiles"][prof] = {"overall": overall, "buckets": buckets(all_fwd),
                                    "by_setup": by_setup, "by_year": by_year,
                                    "fwd_n": len(all_fwd)}
    (ROOT / "backtest.json").write_text(json.dumps(report, separators=(",", ":")), encoding="utf-8")
    write_report(report)
    print("Wrote backtest_report.md and backtest.json")

def fmt(x, p=2):
    if x is None: return "–"
    if x == float("inf"): return "∞"
    return f"{x:.{p}f}"

def write_report(r):
    L = []
    L.append("# IDX Screener — Backtest Report\n")
    L.append(f"_Generated {r['generatedAt']} · {r['tickers']} tickers · history {r['years']} · "
             f"entry score ≥ {r['entryScore']:.0f} · costs {r['cost']*100:.1f}% round-trip_\n")
    L.append("**Trade rules tested:** enter at next open when score ≥ threshold, the setup is tradable "
             "(Oversold Bounce / Avoid / Neutral / Overbought are excluded), and IHSG is **risk-on** "
             "(above its 50-day MA). Exit on a wide **disaster stop** (3×ATR Daily, 3.5× Swing), a daily "
             "**close below the trail MA** (MA10 Daily, MA20 Swing), or a time cap. Compare against the "
             "previous tight-stop version to see the effect.\n")
    L.append("> **Read this first.** Absolute returns are optimistic — the universe is *today's* liquid "
             "names (survivorship bias). The trustworthy signal is **relative**: does expectancy rise with "
             "the score, and which setups beat the average. Scalp uses daily bars (buy-open→sell-close proxy), "
             "so it can't model true intraday timing. Costs/slippage are a flat assumption.\n")
    L.append("## How to read it\n")
    L.append("- **Win rate** = % of trades closed positive. **Expectancy** = average % return per trade "
             "(after costs) — the single most important number; positive = edge. **Avg R** = expectancy in "
             "units of risk (return ÷ initial stop distance); >0.1–0.2 is healthy. **Profit factor** = gross "
             "profit ÷ gross loss; >1.3 is good. **Max DD** = worst peak-to-trough of the cumulative trade P&L.\n")

    for prof in PROFILES:
        p = r["profiles"][prof]; ov = p["overall"]
        L.append(f"\n## {prof.upper()} profile\n")
        L.append("### Does the score predict? (forward-return study, no stops)\n")
        L.append(f"_{p['fwd_n']:,} signal-days, {HORIZON[prof]}-day forward return:_\n")
        L.append("| Score bucket | Samples | Avg fwd return | Hit rate |\n|---|---|---|---|")
        for name, n, avg, hr in p["buckets"]:
            L.append(f"| {name} | {n:,} | {fmt(avg)}% | {fmt(hr,1)}% |")
        L.append("\n_If the score works, average forward return should climb as the bucket rises._\n")
        if ov:
            L.append("\n### Realistic trade simulation\n")
            L.append(f"- Trades: **{ov['n']:,}** · Win rate: **{fmt(ov['winrate'],1)}%** · "
                     f"Expectancy: **{fmt(ov['expectancy'])}%/trade** · Avg R: **{fmt(ov['avg_R'])}** · "
                     f"Profit factor: **{fmt(ov['profit_factor'])}**")
            L.append(f"- Avg win {fmt(ov['avg_win'])}% · Avg loss {fmt(ov['avg_loss'])}% · "
                     f"Avg hold {fmt(ov['avg_hold'],1)} bars · Max drawdown {fmt(ov['max_dd'])}% (cum.)\n")
            L.append("**By setup:**\n")
            L.append("| Setup | Trades | Win% | Expectancy | Avg R | PF |\n|---|---|---|---|---|---|")
            for st, b in sorted(p["by_setup"].items(), key=lambda kv: -(kv[1]["expectancy"] if kv[1] else -9)):
                if b: L.append(f"| {st} | {b['n']:,} | {fmt(b['winrate'],1)} | {fmt(b['expectancy'])}% | {fmt(b['avg_R'])} | {fmt(b['profit_factor'])} |")
            L.append("\n**By year:**\n")
            L.append("| Year | Trades | Win% | Expectancy | Avg R |\n|---|---|---|---|---|")
            for yr, b in p["by_year"].items():
                if b: L.append(f"| {yr} | {b['n']:,} | {fmt(b['winrate'],1)} | {fmt(b['expectancy'])}% | {fmt(b['avg_R'])} |")
        else:
            L.append("\n_No trades triggered at this entry threshold._\n")
    L.append("\n---\n_Backtest is decision-support, not a guarantee. Past performance does not predict future "
             "results. Re-run periodically and trust the relative/ranked findings over absolute returns._\n")
    (ROOT / "backtest_report.md").write_text("\n".join(L), encoding="utf-8")

if __name__ == "__main__":
    main()
