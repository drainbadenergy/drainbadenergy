#!/usr/bin/env python3
"""
Fetches live BTC/ETH prices from CoinGecko's public API and rewrites the
section of README.md between the TICKER:START / TICKER:END markers.

Runs stdlib-only (urllib + json) so the GitHub Action needs no pip install.
"""
import json
import re
import urllib.request
from datetime import datetime, timezone

README_PATH = "README.md"
API_URL = (
    "https://api.coingecko.com/api/v3/simple/price"
    "?ids=bitcoin,ethereum&vs_currencies=usd&include_24hr_change=true"
)
START = "<!--TICKER:START-->"
END = "<!--TICKER:END-->"


def fetch_prices():
    req = urllib.request.Request(API_URL, headers={"User-Agent": "ticker-bot"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read().decode())


def fmt_coin(symbol, data):
    price = data["usd"]
    change = data.get("usd_24h_change", 0)
    arrow = "🟢" if change >= 0 else "🔴"
    return f"{arrow} {symbol} ${price:,.0f} ({change:+.1f}% 24h)"


def build_block(data):
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    line = f"`{fmt_coin('BTC', data['bitcoin'])} · {fmt_coin('ETH', data['ethereum'])}`"
    return (
        f"{START}\n"
        f"### \U0001F4E1 live from the trading terminal\n"
        f"{line} — last refreshed {now}, powered by the same feed "
        f"[TYCHE](#-tyche--crypto-quant-rl-agent) trains on\n"
        f"{END}"
    )


def main():
    with open(README_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    try:
        data = fetch_prices()
        new_block = build_block(data)
    except Exception as exc:  # noqa: BLE001 — keep the workflow green even if the API hiccups
        print(f"price fetch failed, leaving ticker untouched: {exc}")
        return

    pattern = re.compile(re.escape(START) + r".*?" + re.escape(END), re.DOTALL)
    if not pattern.search(content):
        print("markers not found in README.md, nothing to update")
        return

    updated = pattern.sub(new_block, content)
    if updated != content:
        with open(README_PATH, "w", encoding="utf-8") as f:
            f.write(updated)
        print("ticker updated")
    else:
        print("no change")


if __name__ == "__main__":
    main()
