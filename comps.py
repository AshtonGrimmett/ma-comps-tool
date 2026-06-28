import yfinance as yf
import pandas as pd

tickers = {
    "BMW.DE": "BMW",
    "MBG.DE": "Mercedes-Benz Group",
    "VOW3.DE": "Volkswagen",
    "STLA": "Stellantis",
    "F": "Ford",
    "GM": "General Motors",
    "TSLA": "Tesla",
}

rows = []

for ticker, name in tickers.items():
    stock = yf.Ticker(ticker)
    info = stock.info

    market_cap = info.get("marketCap")
    total_debt = info.get("totalDebt")
    cash = info.get("totalCash")
    ebitda = info.get("ebitda")
    revenue = info.get("totalRevenue")

    # Skip if any critical field is missing
    if None in (market_cap, total_debt, cash, ebitda, revenue):
        print(f"Skipping {name} - missing data")
        continue

    enterprise_value = market_cap + total_debt - cash

    ev_ebitda = enterprise_value / ebitda if ebitda else None
    ev_revenue = enterprise_value / revenue if revenue else None

    rows.append({
        "Company": name,
        "Market Cap ($)": market_cap,
        "Total Debt ($)": total_debt,
        "Cash ($)": cash,
        "EV ($)": enterprise_value,
        "EBITDA ($)": ebitda,
        "EV/EBITDA": round(ev_ebitda, 2) if ev_ebitda else None,
        "EV/Revenue": round(ev_revenue, 2) if ev_revenue else None,
    })

df = pd.DataFrame(rows)
print(df.to_string(index=False))

df = pd.DataFrame(rows)

# Flag unreliable multiples (negative EBITDA = not meaningful)
df["EV/EBITDA Flag"] = df["EV/EBITDA"].apply(lambda x: "NM" if x is not None and x < 0 else "")

print("Full comps table:")
print(df.to_string(index=False))

# Exclude NM and Tesla (growth outlier) from summary stats
clean_for_stats = df[(df["EV/EBITDA Flag"] == "") & (df["Company"] != "Tesla")]

summary = {
    "Mean EV/EBITDA": round(clean_for_stats["EV/EBITDA"].mean(), 2),
    "Median EV/EBITDA": round(clean_for_stats["EV/EBITDA"].median(), 2),
    "Min EV/EBITDA": round(clean_for_stats["EV/EBITDA"].min(), 2),
    "Max EV/EBITDA": round(clean_for_stats["EV/EBITDA"].max(), 2),
}

print("\nSummary stats (ex-Tesla, ex-NM):")
for k, v in summary.items():
    print(f"{k}: {v}")
