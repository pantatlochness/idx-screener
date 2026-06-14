# IDX Daily Screener — live on GitHub Pages

A self-updating daily screener for the Indonesia Stock Exchange. Two GitHub
Actions keep it current: one **rebuilds the liquid universe weekly**, the other
**refreshes prices every 15 minutes** during market hours and commits `data.json`.
GitHub Pages serves the dashboard, which loads those files from the same origin
(so there is **no CORS problem** and nothing to configure in your browser).

The screening pool is **every liquid/tradable IDX stock**, built automatically:
the builder takes a seed list plus live-discovered IDX listings, measures each
name's real daily turnover on Yahoo, and keeps only those trading above a
liquidity floor (default Rp1bn/day). New active stocks get added; illiquid or
delisted ones drop out — you don't maintain the list by hand.

## Files

| File | Purpose |
|------|---------|
| `index.html` | The dashboard (scoring engine runs here, in your browser) |
| `tickers.json` | The liquid universe — **auto-generated**, no need to edit |
| `universe_seed.json` | Candidate pool the builder filters by liquidity (edit to add names) |
| `build_tickers.py` | Discovers + liquidity-filters tickers → writes `tickers.json` |
| `fetch_data.py` | Pulls Yahoo `.JK` daily bars → writes `data.json` |
| `data.json` | Auto-generated price snapshot (created by the Action) |
| `.github/workflows/update.yml` | Refreshes prices every 15 min (market hours) |
| `.github/workflows/build-universe.yml` | Rebuilds the liquid universe weekly |

> **Not financial advice.** Data is delayed/free and may differ from your broker.
> Confirm price, bid/ask and broker summary in your terminal before trading.

---

## Deploy in ~5 minutes

### 1. Create the repository
**Easiest (web upload):** create a new repo at github.com → **Add file → Upload
files** → drag in `index.html`, `tickers.json`, `universe_seed.json`,
`fetch_data.py`, `build_tickers.py`, and the `.github` folder → Commit.

**Or with Git:**
```bash
cd screener
git init && git add . && git commit -m "IDX screener"
git branch -M main
git remote add origin https://github.com/<you>/<repo>.git
git push -u origin main
```

### 2. Allow the Action to commit data
Repo **Settings → Actions → General → Workflow permissions** → select
**Read and write permissions** → Save. (Without this the job can't push `data.json`.)

### 3. Turn on GitHub Pages
Repo **Settings → Pages** → Source = **Deploy from a branch** → Branch = **main**,
folder **/ (root)** → Save. Your URL appears as
`https://<you>.github.io/<repo>/`.

### 4. Build the universe, then the first prices
In the **Actions** tab, run these once (each: click the workflow → **Run workflow**):
1. **Rebuild liquid universe** — expands `tickers.json` to the full liquid pool
   (~3–5 min). Optional but recommended on day one; otherwise it first runs Sunday.
2. **Update IDX data** — creates the first `data.json` (~2–4 min).

Then open your Pages URL — the screener loads and ranks automatically.

---

## How updates work
- **Prices:** *Update IDX data* runs **every ~15 min during IDX hours**
  (Mon–Fri, 02:00–09:00 UTC = 09:00–16:00 WIB) and on manual trigger.
- **Universe:** *Rebuild liquid universe* runs **weekly** (Sun 22:00 UTC) — new
  liquid stocks in, illiquid/delisted out. Adjust the liquidity floor when running
  it manually (the `liq_min_idr` input).
- The open dashboard re-pulls `data.json` every 5 minutes, so a tab left open
  stays current. The status bar shows **"data as of …"**.

### Good to know
- GitHub cron is *best-effort* and can be delayed a few minutes — fine for daily
  trading, not for tick-level timing.
- GitHub **disables scheduled workflows after 60 days of no repo activity** — just
  push any commit (or hit Run workflow) to re-arm them.
- Yahoo occasionally rate-limits cloud IPs. If a run shows many "failed" tickers,
  re-run it; the dashboard still works on whatever came back, and you can switch
  Data mode to **Live browser fetch** as a fallback.
- **Repo size:** `data.json` is committed every 15 min, so history grows over
  months. To reset it occasionally, you can squash history or re-create the repo;
  it has no effect on the live site.

## Using the dashboard
- **Data mode** → keep on *GitHub snapshot* when hosted. *Live browser fetch* and
  *Load demo data* are fallbacks.
- Filter by **min score, setup, sector, liquidity**; set **capital** and **risk %**
  to get suggested lot sizes. Click any row for the full breakdown + chart.
- **Bandarmology box** — free data has no broker summary, so paste tickers showing
  foreign net-buy/accumulation from your terminal to boost their score.

## Customising
- Add candidate stocks: add codes to `universe_seed.json` (grouped by sector).
  They're included automatically once they pass the liquidity test. Don't edit
  `tickers.json` directly — the weekly build overwrites it.
- Change the liquidity floor: edit `LIQ_MIN_IDR` (or pass `liq_min_idr` when
  running the universe workflow). Lower = more (smaller) names included.
- Change price update frequency: edit the `cron` line in `update.yml`.
- Tune scoring: edit the `analyze()` weights in `index.html`.
