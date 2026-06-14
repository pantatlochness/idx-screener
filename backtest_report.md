# IDX Screener — Backtest Report

_Generated 2026-06-14T18:26:18+00:00 · 159 tickers · history 3y · entry score ≥ 65 · costs 0.3% round-trip_

**Trade rules tested:** enter at next open when score ≥ threshold, the setup is tradable (Oversold Bounce / Avoid / Neutral / Overbought are excluded), and IHSG is **risk-on** (above its 50-day MA). Exit on a wide **disaster stop** (3×ATR Daily, 3.5× Swing), a daily **close below the trail MA** (MA10 Daily, MA20 Swing), or a time cap. Compare against the previous tight-stop version to see the effect.

> **Read this first.** Absolute returns are optimistic — the universe is *today's* liquid names (survivorship bias). The trustworthy signal is **relative**: does expectancy rise with the score, and which setups beat the average. Scalp uses daily bars (buy-open→sell-close proxy), so it can't model true intraday timing. Costs/slippage are a flat assumption.

## How to read it

- **Win rate** = % of trades closed positive. **Expectancy** = average % return per trade (after costs) — the single most important number; positive = edge. **Avg R** = expectancy in units of risk (return ÷ initial stop distance); >0.1–0.2 is healthy. **Profit factor** = gross profit ÷ gross loss; >1.3 is good. **Max DD** = worst peak-to-trough of the cumulative trade P&L.


## DAILY profile

### Does the score predict? (forward-return study, no stops)

_90,254 signal-days, 5-day forward return:_

| Score bucket | Samples | Avg fwd return | Hit rate |
|---|---|---|---|
| 0-49 | 66,578 | 0.01% | 44.2% |
| 50-59 | 7,978 | 0.36% | 45.0% |
| 60-69 | 6,474 | 0.59% | 45.2% |
| 70-79 | 4,318 | 0.63% | 44.8% |
| 80-100 | 4,906 | 1.05% | 44.6% |

_If the score works, average forward return should climb as the bucket rises._


### Realistic trade simulation

- Trades: **2,114** · Win rate: **30.1%** · Expectancy: **0.38%/trade** · Avg R: **0.00** · Profit factor: **1.12**
- Avg win 12.05% · Avg loss -4.64% · Avg hold 6.2 bars · Max drawdown -416.52% (cum.)

**By setup:**

| Setup | Trades | Win% | Expectancy | Avg R | PF |
|---|---|---|---|---|---|
| Momentum Breakout | 1,183 | 30.4 | 0.78% | 0.03 | 1.22 |
| Pullback Buy | 119 | 27.7 | 0.45% | 0.05 | 1.18 |
| Trend Continuation | 605 | 30.1 | -0.02% | -0.02 | 0.99 |
| Breakout Watch | 207 | 29.5 | -0.76% | -0.06 | 0.76 |

**By year:**

| Year | Trades | Win% | Expectancy | Avg R |
|---|---|---|---|---|
| 2023 | 211 | 28.9 | -0.47% | -0.08 |
| 2024 | 865 | 30.1 | -0.13% | -0.01 |
| 2025 | 912 | 30.5 | 1.35% | 0.06 |
| 2026 | 126 | 29.4 | -1.73% | -0.14 |

## SWING profile

### Does the score predict? (forward-return study, no stops)

_89,489 signal-days, 10-day forward return:_

| Score bucket | Samples | Avg fwd return | Hit rate |
|---|---|---|---|
| 0-49 | 56,759 | 0.10% | 44.3% |
| 50-59 | 4,863 | 0.09% | 42.8% |
| 60-69 | 4,654 | 0.29% | 43.2% |
| 70-79 | 6,445 | 0.58% | 43.5% |
| 80-100 | 16,768 | 0.94% | 43.9% |

_If the score works, average forward return should climb as the bucket rises._


### Realistic trade simulation

- Trades: **2,031** · Win rate: **26.7%** · Expectancy: **1.06%/trade** · Avg R: **0.04** · Profit factor: **1.30**
- Avg win 17.26% · Avg loss -4.83% · Avg hold 10.4 bars · Max drawdown -449.99% (cum.)

**By setup:**

| Setup | Trades | Win% | Expectancy | Avg R | PF |
|---|---|---|---|---|---|
| Uptrend – Hold | 609 | 27.6 | 1.34% | 0.04 | 1.40 |
| Swing Buy – Breakout | 802 | 27.8 | 1.19% | 0.04 | 1.27 |
| Swing Buy – Pullback | 607 | 24.5 | 0.76% | 0.03 | 1.30 |
| Base / Accumulation | 8 | 12.5 | -3.24% | -0.33 | 0.19 |
| Uptrend – Extended | 5 | 20.0 | -8.19% | -0.51 | 0.06 |

**By year:**

| Year | Trades | Win% | Expectancy | Avg R |
|---|---|---|---|---|
| 2023 | 238 | 21.8 | -0.61% | -0.09 |
| 2024 | 841 | 26.0 | 0.18% | -0.00 |
| 2025 | 833 | 29.3 | 2.86% | 0.14 |
| 2026 | 119 | 22.7 | -1.94% | -0.17 |

## SCALP profile

### Does the score predict? (forward-return study, no stops)

_90,857 signal-days, 1-day forward return:_

| Score bucket | Samples | Avg fwd return | Hit rate |
|---|---|---|---|
| 0-49 | 55,415 | 0.03% | 40.4% |
| 50-59 | 14,588 | 0.05% | 41.7% |
| 60-69 | 9,914 | 0.02% | 40.9% |
| 70-79 | 5,831 | -0.01% | 40.1% |
| 80-100 | 5,109 | 0.08% | 39.0% |

_If the score works, average forward return should climb as the bucket rises._


### Realistic trade simulation

- Trades: **4,803** · Win rate: **33.8%** · Expectancy: **-0.60%/trade** · Avg R: **-0.15** · Profit factor: **0.74**
- Avg win 5.18% · Avg loss -3.56% · Avg hold 0.8 bars · Max drawdown -2910.18% (cum.)

**By setup:**

| Setup | Trades | Win% | Expectancy | Avg R | PF |
|---|---|---|---|---|---|
| Scalp – Volatile mover | 3,224 | 36.0 | -0.52% | -0.12 | 0.77 |
| Scalp – Momentum | 1,579 | 29.3 | -0.79% | -0.21 | 0.69 |

**By year:**

| Year | Trades | Win% | Expectancy | Avg R |
|---|---|---|---|---|
| 2023 | 471 | 31.4 | -0.62% | -0.19 |
| 2024 | 1,514 | 33.8 | -0.68% | -0.18 |
| 2025 | 2,367 | 34.5 | -0.41% | -0.11 |
| 2026 | 451 | 33.0 | -1.36% | -0.24 |

---
_Backtest is decision-support, not a guarantee. Past performance does not predict future results. Re-run periodically and trust the relative/ranked findings over absolute returns._
