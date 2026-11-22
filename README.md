# pp-prices

Daily EUR/oz price feeds for [Portfolio Performance](https://www.portfolio-performance.info/), built from Yahoo Finance data and updated every weekday by GitHub Actions.

| File | What it is |
|---|---|
| `prices/gold_eur_oz.json` | Gold: COMEX front-month (`GC=F`) / `EURUSD=X` |
| `prices/silver_coin_eur_oz.json` | Silver 1 oz coin, dealer-buyback value: `SI=F` / `EURUSD=X` × `SILVER_COIN_FACTOR` |

The silver multiplier is set in `metals_prices.py`. It was calibrated on 2026-11-22 against a Czech dealer's VIP buyback price for the Maple Leaf 1 oz; re-check it from time to time.

## PP setup

Security → Historical Quotes → provider **JSON**:

- URL: `https://raw.githubusercontent.com/jakub-zovi/pp-prices/main/prices/<file>.json`
- Path to date: `$[*].d`
- Path to close: `$[*].v`
- Date format: `yyyy-MM-dd`

## Run locally

```bash
python3 metals_prices.py            # 10 years of history into prices/
python3 metals_prices.py --range max
```
