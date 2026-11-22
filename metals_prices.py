"""Build EUR/oz gold and silver-coin price feeds for Portfolio Performance.

Source: Yahoo Finance chart API (same endpoint PP's own Yahoo feed uses).
  GC=F      COMEX gold futures, front month, USD/oz
  SI=F      COMEX silver futures, front month, USD/oz
  EURUSD=X  EUR/USD rate (USD per 1 EUR)

Output (PP "GENERIC-JSON" feed format):
  [{"d": "yyyy-MM-dd", "v": 1234.56}, ...]
PP feed settings: date path `$[*].d`, close path `$[*].v`, date format `yyyy-MM-dd`.

Silver coin value = silver spot (EUR) x SILVER_COIN_FACTOR, a dealer-buyback
multiplier. Calibrated 2026-11-22 from Zlataky VIP buyback of Maple Leaf 1 oz
(800 CZK vs. spot ~914 CZK). Re-check every few months:
https://stribrnaky.zlataky.cz/vykup-stribra

Usage: python metals_prices.py [--out DIR] [--range 10y]
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import time
import urllib.request
from pathlib import Path

SILVER_COIN_FACTOR = 0.875

YAHOO_URL = "https://query1.finance.yahoo.com/v8/finance/chart/{ticker}?range={range}&interval=1d"
DEFAULT_OUT = Path(__file__).resolve().parent / "prices"


def fetch_yahoo(ticker: str, range_: str) -> dict[str, float]:
    """Return {yyyy-mm-dd: close} for a Yahoo ticker."""
    url = YAHOO_URL.format(ticker=ticker, range=range_)
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                chart = json.load(resp)["chart"]
            break
        except Exception:
            if attempt == 2:
                raise
            time.sleep(5 * (attempt + 1))
    if chart.get("error") or not chart.get("result"):
        raise RuntimeError(f"Yahoo returned no data for {ticker}: {chart.get('error')}")
    res = chart["result"][0]
    # Exchange-local date (futures trade in New York; avoids UTC date shifts).
    offset = res["meta"].get("gmtoffset", 0)
    closes = res["indicators"]["quote"][0]["close"]
    out: dict[str, float] = {}
    for ts, close in zip(res["timestamp"], closes):
        if close is None:
            continue
        day = dt.datetime.fromtimestamp(ts + offset, dt.timezone.utc).date().isoformat()
        out[day] = close
    if not out:
        raise RuntimeError(f"No closes for {ticker}")
    return out


def to_eur(usd: dict[str, float], eurusd: dict[str, float], factor: float = 1.0) -> list[dict]:
    """Convert USD prices to EUR using the same-day rate (or the last known one)."""
    fx_days = sorted(eurusd)
    rows, i, rate = [], 0, None
    for day in sorted(usd):
        while i < len(fx_days) and fx_days[i] <= day:
            rate = eurusd[fx_days[i]]
            i += 1
        if rate is None:
            continue  # no FX rate yet for this early date
        rows.append({"d": day, "v": round(usd[day] / rate * factor, 2)})
    return rows


def write_json(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(rows, separators=(",", ":")) + "\n")
    print(f"{path.name}: {len(rows)} rows, {rows[0]['d']} .. {rows[-1]['d']} = {rows[-1]['v']} EUR")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT)
    ap.add_argument("--range", default="10y", help="Yahoo range, e.g. 1mo, 1y, 10y, max")
    args = ap.parse_args()

    eurusd = fetch_yahoo("EURUSD=X", args.range)
    gold = fetch_yahoo("GC=F", args.range)
    silver = fetch_yahoo("SI=F", args.range)

    write_json(args.out / "gold_eur_oz.json", to_eur(gold, eurusd))
    write_json(args.out / "silver_coin_eur_oz.json", to_eur(silver, eurusd, SILVER_COIN_FACTOR))


if __name__ == "__main__":
    main()
