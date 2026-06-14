# IDX Screener — Backtest Report

_Generated 2026-06-14T17:53:22+00:00 · 159 tickers · history 3y · entry score ≥ 65 · costs 0.3% round-trip_

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

- Trades: **4,387** · Win rate: **38.3%** · Expectancy: **-0.43%/trade** · Avg R: **-0.10** · Profit factor: **0.86**
- Avg win 7.09% · Avg loss -5.09% · Avg hold 3.3 bars · Max drawdown -1897.24% (cum.)

**By setup:**

| Setup | Trades | Win% | Expectancy | Avg R | PF |
|---|---|---|---|---|---|
| Overbought – caution | 295 | 44.7 | 0.95% | 0.10 | 1.25 |
| Trend Continuation | 1,427 | 39.0 | -0.13% | -0.07 | 0.96 |
| Neutral / No setup | 142 | 39.4 | -0.42% | -0.07 | 0.86 |
| Pullback Buy | 188 | 35.6 | -0.66% | -0.19 | 0.73 |
| Breakout Watch | 379 | 37.7 | -0.69% | -0.14 | 0.76 |
| Momentum Breakout | 1,892 | 37.5 | -0.72% | -0.13 | 0.77 |
| Oversold Bounce | 64 | 26.6 | -2.55% | -0.29 | 0.50 |

**By year:**

| Year | Trades | Win% | Expectancy | Avg R |
|---|---|---|---|---|
| 2023 | 383 | 32.1 | -0.91% | -0.20 |
| 2024 | 1,627 | 39.1 | -0.40% | -0.07 |
| 2025 | 1,743 | 40.0 | -0.01% | -0.06 |
| 2026 | 634 | 35.2 | -1.33% | -0.21 |

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

- Trades: **3,398** · Win rate: **34.4%** · Expectancy: **-0.36%/trade** · Avg R: **-0.08** · Profit factor: **0.92**
- Avg win 12.16% · Avg loss -6.92% · Avg hold 8.8 bars · Max drawdown -1252.65% (cum.)

**By setup:**

| Setup | Trades | Win% | Expectancy | Avg R | PF |
|---|---|---|---|---|---|
| Uptrend – Extended | 72 | 43.1 | 0.49% | 0.07 | 1.08 |
| Swing Buy – Pullback | 645 | 33.6 | -0.04% | -0.06 | 0.99 |
| Swing Buy – Breakout | 1,229 | 35.3 | -0.37% | -0.08 | 0.92 |
| Uptrend – Hold | 1,142 | 34.7 | -0.37% | -0.09 | 0.92 |
| Neutral / No setup | 228 | 31.6 | -0.54% | 0.06 | 0.88 |
| Base / Accumulation | 11 | 45.5 | -1.13% | -0.18 | 0.65 |
| Avoid – Downtrend | 71 | 19.7 | -3.06% | -0.51 | 0.45 |

**By year:**

| Year | Trades | Win% | Expectancy | Avg R |
|---|---|---|---|---|
| 2023 | 308 | 29.2 | -1.03% | -0.15 |
| 2024 | 1,244 | 35.3 | -0.48% | -0.09 |
| 2025 | 1,355 | 39.4 | 1.10% | 0.09 |
| 2026 | 491 | 21.6 | -3.65% | -0.45 |

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

- Trades: **9,325** · Win rate: **28.8%** · Expectancy: **-0.87%/trade** · Avg R: **-0.30** · Profit factor: **0.58**
- Avg win 4.23% · Avg loss -2.93% · Avg hold 0.5 bars · Max drawdown -8105.94% (cum.)

**By setup:**

| Setup | Trades | Win% | Expectancy | Avg R | PF |
|---|---|---|---|---|---|
| Scalp – Volatile mover | 5,872 | 29.2 | -0.71% | -0.27 | 0.64 |
| Watch | 484 | 26.0 | -0.79% | -0.45 | 0.38 |
| Avoid – Too thin/quiet | 409 | 28.6 | -1.00% | -0.26 | 0.59 |
| Scalp – Momentum | 2,560 | 28.5 | -1.24% | -0.34 | 0.49 |

**By year:**

| Year | Trades | Win% | Expectancy | Avg R |
|---|---|---|---|---|
| 2023 | 801 | 27.1 | -1.05% | -0.38 |
| 2024 | 2,854 | 30.4 | -0.69% | -0.26 |
| 2025 | 3,850 | 29.5 | -0.78% | -0.29 |
| 2026 | 1,820 | 25.7 | -1.25% | -0.35 |

---
_Backtest is decision-support, not a guarantee. Past performance does not predict future results. Re-run periodically and trust the relative/ranked findings over absolute returns._
