import random
import statistics
from collections import deque

# Practice companies. These are made up, and prices are simulated on this computer,
# so the whole market works without internet.
# vol   = how much the price jumps around every second
# trend = small long term push (positive means the company slowly grows)
# beta  = how strongly the stock follows the whole market
STOCKS = [
    {"symbol": "TCNX", "name": "TechNova Systems", "sector": "IT",
     "price": 1850.0, "vol": 0.0016, "trend": 0.00004, "beta": 1.3,
     "risk": "Medium", "dividend": 0.8},
    {"symbol": "FINB", "name": "FinBridge Bank", "sector": "Banking",
     "price": 1420.0, "vol": 0.0011, "trend": 0.00002, "beta": 1.0,
     "risk": "Low", "dividend": 1.6},
    {"symbol": "GRNP", "name": "GreenPower Energy", "sector": "Energy",
     "price": 310.0, "vol": 0.0022, "trend": 0.00005, "beta": 1.5,
     "risk": "High", "dividend": 0.4},
    {"symbol": "MEDC", "name": "MediCure Pharma", "sector": "Pharma",
     "price": 960.0, "vol": 0.0012, "trend": 0.00003, "beta": 0.7,
     "risk": "Low", "dividend": 1.2},
    {"symbol": "AUTX", "name": "AutoMax Motors", "sector": "Auto",
     "price": 720.0, "vol": 0.0018, "trend": 0.00003, "beta": 1.4,
     "risk": "Medium", "dividend": 1.0},
    {"symbol": "FMGO", "name": "FreshMart Foods", "sector": "FMCG",
     "price": 2400.0, "vol": 0.0008, "trend": 0.00002, "beta": 0.5,
     "risk": "Low", "dividend": 2.1},
    {"symbol": "SKYR", "name": "SkyLine Realty", "sector": "Real Estate",
     "price": 540.0, "vol": 0.0024, "trend": 0.00002, "beta": 1.6,
     "risk": "High", "dividend": 0.6},
    {"symbol": "GLDV", "name": "GoldVault Metals", "sector": "Metals",
     "price": 640.0, "vol": 0.0013, "trend": 0.00003, "beta": 0.6,
     "risk": "Medium", "dividend": 1.4},
]


class Market:
    HISTORY = 120  # how many seconds of price history we keep for the graphs

    def __init__(self):
        self.stocks = {}
        for s in STOCKS:
            stock = dict(s)
            stock["base"] = s["price"]
            stock["open"] = s["price"]
            stock["history"] = deque(maxlen=self.HISTORY)
            self.stocks[s["symbol"]] = stock
        # run the market for a while first so the graphs are not empty at the start
        for _ in range(self.HISTORY):
            self.tick()
        for stock in self.stocks.values():
            stock["open"] = stock["price"]  # "since open" starts counting from now

    def symbols(self):
        return list(self.stocks.keys())

    def tick(self):
        # called once every second: moves every price a little up or down
        market_move = random.gauss(0, 0.0008)  # the whole market moves together
        for stock in self.stocks.values():
            move = stock["trend"]
            move += market_move * stock["beta"]
            move += random.gauss(0, stock["vol"])
            # gently pulls the price back so it never runs away during a demo
            move += (stock["base"] - stock["price"]) / stock["base"] * 0.003
            # now and then a "news event" gives a bigger jump
            if random.random() < 0.003:
                move += random.choice([-1, 1]) * random.uniform(0.004, 0.012)
            stock["price"] = max(1.0, round(stock["price"] * (1 + move), 2))
            stock["history"].append(stock["price"])

    # ----- simple questions about a stock -----
    def price(self, symbol):
        return self.stocks[symbol]["price"]

    def change_pct(self, symbol):
        # change since the market opened (since the app started)
        stock = self.stocks[symbol]
        return (stock["price"] / stock["open"] - 1) * 100

    def momentum(self, symbol, seconds=60):
        # change over the last few seconds, in percent
        history = list(self.stocks[symbol]["history"])
        past = history[max(0, len(history) - 1 - seconds)]
        return (history[-1] / past - 1) * 100

    def volatility(self, symbol):
        # how bumpy the price has been, as a percent per second
        history = list(self.stocks[symbol]["history"])
        moves = [(history[i] / history[i - 1] - 1) * 100 for i in range(1, len(history))]
        return statistics.pstdev(moves) if moves else 0.0

    def index_value(self):
        # one number for the whole market (it starts near 1000)
        total = sum(s["price"] / s["base"] for s in self.stocks.values())
        return total / len(self.stocks) * 1000

    def index_change(self):
        total_now = sum(s["price"] / s["open"] for s in self.stocks.values())
        return (total_now / len(self.stocks) - 1) * 100