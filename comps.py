import yfinance as yf

tickers = {
    "BMW.DE": "BMW",
    "MBG.DE": "Mercedes-Benz Group",
    "VOW3.DE": "Volkswagen",
    "STLA": "Stellantis",
    "F": "Ford",
    "GM": "General Motors",
    "TSLA": "Tesla",
}

for ticker, name in tickers.items():
    stock = yf.Ticker(ticker)
    info = stock.info
    print(name, "| Market Cap:", info.get("marketCap"))