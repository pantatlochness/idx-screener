# IDX Daily Screener — live on GitHub Pages

A self-updating daily screener for the Indonesia Stock Exchange. A GitHub Action
fetches fresh prices on a schedule and commits `data.json`; GitHub Pages serves
the dashboard, which loads that snapshot from the same origin (so there is **no
CORS problem** and nothing to configure in your browser).

## Files

| File | Purpose |
|------|---------|
| `index.html` | The dashboard (scoring engine runs here, in your browser) |
| `tickers.json` | The liquid universe — edit this to add/remove stocks |
| `fetch_data.py` | Pulls Yahoo `.JK` daily bars → writes `data.json` |
| `data.json` | Auto-generated price snapshot (created by the Action) |
| `.github/workflows/update.yml` | Scheduled job that refreshes `data.json` |

> **Not financial advice.** Data is delayed/free and may differ from your broker.
> Confirm price, bid/ask and broker summary in your terminal before trading.

---

## Deploy in ~5 minutes

### 1. Create the repository
**Easiest (web upload):** create a new repo at github.com → **Add file → Upload
files** → drag in `index.html`, `tickers.json`, `fetch_data.py`, and the
`.github` folder → Commit.

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

### 4. Generate the first snapshot
Repo **Actions** tab → **Update IDX data** → **Run workflow**. After it finishes
(~1–2 min) a `data.json` commit appears. Open your Pages URL — the screener loads
and ranks automatically.

---

## How updates work
- The Action runs **every ~15 min during IDX hours** (Mon–Fri, 02:00–09:00 UTC =
  09:00–16:00 WIB) and on manual trigger.
- The open dashboard re-pulls `data.json` every 5 minutes, so a tab left open
  stays current. The status bar shows **"data as of …"**.

### Good to know
- GitHub cron is *best-effort* and can be delayed a few minutes — fine for daily
  trading, not for tick-level timing.
- GitHub **disables scheduled workflows after 60 days of no repo activity** — just
  push any commit (or hit Run workflow) to re-arm it.
- Yahoo occasionally rate-limits cloud IPs. If a run shows many "failed" tickers,
  re-run it; the dashboard still works on whatever came back, and you can switch
  Data mode to **Live browser fetch** as a fallback.

## Using the dashboard
- **Data mode** → keep on *GitHub snapshot* when hosted. *Live browser fetch* and
  *Load demo data* are fallbacks.
- Filter by **min score, setup, sector, liquidity**; set **capital** and **risk %**
  to get suggested lot sizes. Click any row for the full breakdown + chart.
- **Bandarmology box** — free data has no broker summary, so paste tickers showing
  foreign net-buy/accumulation from your terminal to boost their score.

## Customising
- Add/remove stocks: edit `tickers.json` (rows are `["SYMBOL","Name","Sector"]`),
  commit — both the fetcher and dashboard pick it up.
- Change update frequency: edit the `cron` line in `.github/workflows/update.yml`.
- Tune scoring: edit the `analyze()` weights in `index.html`.
