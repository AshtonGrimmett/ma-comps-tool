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
    "TM": "Toyota",
    "HMC": "Honda",
    "RACE": "Ferrari",
    "MGA": "Magna International",
    "APTV": "Aptiv",
    "BWA": "BorgWarner",
    "ALV": "Autoliv",
    "LEA": "Lear Corporation",
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

# --- Test the comps method: value BMW using ONLY its peers ---

target_name = "BMW"

# Peer group = everyone except the target, and exclude NM multiples and Tesla (growth outlier)
peer_group = df[
    (df["Company"] != target_name) &
    (df["Company"] != "Tesla") &
    (df["EV/EBITDA Flag"] == "")
]

peer_median_multiple = peer_group["EV/EBITDA"].median()

print(f"\n--- Testing comps method on {target_name} ---")
print(f"Peer group used: {peer_group['Company'].tolist()}")
print(f"Peer median EV/EBITDA (excluding {target_name}): {round(peer_median_multiple, 2)}")

# Get BMW's actual EBITDA and actual EV from our table
target_row = df[df["Company"] == target_name].iloc[0]
target_ebitda = target_row["EBITDA ($)"]
actual_ev = target_row["EV ($)"]

# Apply the peer multiple to BMW's own EBITDA
implied_ev = peer_median_multiple * target_ebitda

print(f"\n{target_name} actual EBITDA: ${target_ebitda:,.0f}")
print(f"{target_name} actual EV (from market data): ${actual_ev:,.0f}")
print(f"{target_name} implied EV (peer median x EBITDA): ${implied_ev:,.0f}")

difference_pct = ((implied_ev - actual_ev) / actual_ev) * 100
print(f"\nDifference: {difference_pct:+.1f}% (implied vs actual)")


with pd.ExcelWriter("comps_output.xlsx", engine="openpyxl") as writer:
    df.to_excel(writer, sheet_name="Comps Table", index=False)

print("\nSaved comps table to comps_output.xlsx")

import matplotlib.pyplot as plt

chart_df = df[df["EV/EBITDA Flag"] == ""].sort_values("EV/EBITDA")

plt.figure(figsize=(10, 6))
plt.barh(chart_df["Company"], chart_df["EV/EBITDA"])
plt.xlabel("EV/EBITDA")
plt.title("Auto Sector: EV/EBITDA Comparison")
plt.tight_layout()
plt.savefig("ev_ebitda_chart.png")
plt.show()

print("Saved chart to ev_ebitda_chart.png")