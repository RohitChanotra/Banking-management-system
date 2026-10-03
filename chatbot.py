import re
import database as db


def money(value):
    return f"Rs. {value:,.2f}"


def tokenize(text):
    # lower case words, plus the singular form of plural words (stocks -> stock)
    words = re.findall(r"[a-z0-9]+", text.lower().replace("'", ""))
    extra = [w[:-1] for w in words if len(w) > 3 and w.endswith("s")]
    return words + extra


def has_all(phrase, words):
    return all(w in words for w in phrase.split())


# ---------------------------------------------------------------------------
# 1. How to use the app. Each guide: (name, key phrases, answer).
#    The guide with the most matching words wins; on a tie the earlier one wins.
# ---------------------------------------------------------------------------
GUIDES = [
    ("admin", ["admin", "administrator"],
     "Admin login is for bank staff only. On the login page click 'Admin login'. "
     "The admin can see all accounts, reset a PIN, unlock a locked account and "
     "delete an account. I can't share the staff login details."),

    ("create", ["create account", "new account", "open account", "register",
                "signup", "sign up", "make account", "naya account"],
     "To create an account:\n"
     "1. On the login page click 'Create new account'.\n"
     "2. Enter your full name, a 10 digit phone number and a 4 digit PIN (twice).\n"
     "3. Click 'Create account'.\n"
     "You will see your account number. Numbers start from 00001. You need the "
     "account number and your PIN to log in."),

    ("security", ["pin safe", "money safe", "data safe", "secure", "security",
                  "hash", "hashed", "encrypted", "encryption", "protected"],
     "Your PIN is never stored as it is typed. It is scrambled (hashed with a random "
     "salt), so nobody, not even the admin, can read it. An account locks after 3 "
     "wrong PINs, and a transfer is saved as one step: either both accounts change "
     "or neither does."),

    ("pin", ["forgot pin", "forget pin", "lost pin", "reset pin", "change pin",
             "locked", "lock", "wrong pin", "pin"],
     "If you forgot your PIN or your account is locked (3 wrong PINs), ask the admin. "
     "In 'Admin login' the admin selects your account and clicks 'Reset PIN' (this "
     "also unlocks it) or 'Unlock account'. The old PIN can't be shown to anyone "
     "because it is stored scrambled. A 'change PIN' screen is not part of this version."),

    ("deposit", ["deposit", "jama", "add money", "add cash", "put money"],
     "To deposit money:\n"
     "1. Click 'Deposit' in the left menu.\n"
     "2. Type the amount.\n"
     "3. Click 'Deposit'.\n"
     "The money is added to your balance and the deposit appears in your Statement."),

    ("withdraw", ["withdraw", "withdrawal", "nikalna", "nikal", "cash out",
                  "take money out"],
     "To withdraw money:\n"
     "1. Click 'Withdraw' in the left menu.\n"
     "2. Type the amount.\n"
     "3. Click 'Withdraw'.\n"
     "You can't withdraw more than your balance."),

    ("transfer", ["transfer", "send money", "send", "bhej", "bhejna", "pay someone"],
     "To transfer money to another AR Bank account:\n"
     "1. Click 'Transfer' in the left menu.\n"
     "2. Enter the receiver's account number and the amount.\n"
     "3. Click 'Send money'. A box shows the receiver's name so you can check it, "
     "then confirm.\n"
     "The receiver must have an account here. Both people see the transfer in their Statement."),

    ("trade", ["buy", "sell", "purchase", "trade", "trading", "khareed", "kharid",
               "bech", "bechna", "bechte", "khareedte", "kharidte", "khareedna",
               "kharidna", "buy stock", "sell stock", "buy share", "sell share"],
     "To buy or sell a stock:\n"
     "1. Click 'Stocks' in the left menu.\n"
     "2. Click a company in 'Market watch'. Its live graph appears on the right.\n"
     "3. Type the number of shares in the 'Shares' box.\n"
     "4. Click 'Buy' (or 'Sell') and confirm the box.\n"
     "Buying takes the money from your account balance at the price shown. Selling "
     "puts the money back. You can only sell shares you own. Every trade appears in "
     "your Statement."),

    ("portfolio", ["portfolio", "holding", "my share"],
     "Your portfolio is the table at the bottom of the 'Stocks' page. It shows each "
     "stock you own, your average buy price, the current price, the value and your "
     "profit or loss. The Home page also shows the total value of your stocks."),

    ("stocks", ["stock market", "stocks page", "graph", "chart", "prices", "live price",
                "practice market"],
     "The 'Stocks' page is a practice stock market with 8 made-up companies. Prices "
     "change every second, they are simulated on this computer, so it works without "
     "internet. Click a company to see its live graph. The dashed line on the graph "
     "is the price when the market opened. The AR Index at the top is one number for "
     "the whole market."),

    ("statement", ["statement", "history", "transaction", "passbook"],
     "Click 'Statement' in the left menu. It lists every transaction, newest first, "
     "with the date, type, amount, balance after it and a note. A + means money came "
     "in and a - means money went out."),

    ("balance", ["balance"],
     "Your balance is on the Home page in the 'Available balance' card. You can also "
     "just ask me 'what is my balance'."),

    ("logout", ["logout", "log out", "sign out", "signout"],
     "Click 'Logout' at the bottom of the left menu."),

    ("login", ["login", "log in", "sign in", "signin", "password"],
     "On the first page type your account number and your 4 digit PIN, then click "
     "Login. After 3 wrong PINs the account locks and the admin has to unlock it."),
]


def find_guide(words):
    best = None
    best_score = 0
    for name, phrases, answer in GUIDES:
        score = sum(len(p.split()) for p in phrases if has_all(p, words))
        if score > best_score:
            best = answer
            best_score = score
    return best


# ---------------------------------------------------------------------------
# 2. Simple explanations of money words
# ---------------------------------------------------------------------------
CONCEPTS = [
    (["dividend"],
     "A dividend is a part of a company's profit that it pays to its shareholders. "
     "A dividend of 2% means about Rs. 2 a year for every Rs. 100 you have invested. "
     "Companies with a higher dividend are often steadier."),
    (["diversification", "diversify", "diversified"],
     "Diversification means not putting all your money in one place. If you own "
     "2 or 3 different companies (from different sectors), one falling price hurts "
     "you less."),
    (["volatility", "volatile", "risk", "risky"],
     "Risk (or volatility) is how much a price jumps up and down. A high risk stock "
     "can give a big profit quickly but can also fall quickly. A low risk stock moves "
     "slowly and steadily. In this app each company is marked Low, Medium or High risk."),
    (["profit", "loss"],
     "Profit or loss is the difference between what a share is worth now and what you "
     "paid for it. If you bought at 100 and it is 110 now, you have a profit of 10 per "
     "share. It only becomes real when you sell."),
    (["index"],
     "The AR Index is one number that shows how the whole practice market is doing. "
     "It is the average of all 8 companies. It starts near 1000 and moves up when most "
     "stocks rise."),
    (["portfolio"],
     "A portfolio is the collection of all the stocks you own."),
    (["simulation", "simulated", "fake", "real"],
     "The companies and prices in this app are made up. A small program on this "
     "computer moves every price a little every second, so the market works without "
     "internet. It is for learning and for the project demo, not for real investing."),
    (["stock", "share", "equity"],
     "A share (or stock) is a small piece of ownership in a company. When the company "
     "does well the price usually goes up, and you can sell your shares for more than "
     "you paid. If it does badly the price can go down."),
]

RECOMMEND_WORDS = {"best", "should", "recommend", "suggest", "top", "good", "better",
                   "worth", "pick", "invest", "kaunsa", "konsa"}


# ---------------------------------------------------------------------------
# 3. Words that describe what the user wants from a stock
# ---------------------------------------------------------------------------
SAFE_PHRASES = ["low risk", "less risk", "safe", "safer", "safest", "secure", "stable",
                "steady", "conservative", "careful", "beginner", "no risk"]
GROWTH_PHRASES = ["high risk", "risky", "aggressive", "growth", "fast", "quick profit",
                  "more profit", "high return", "high reward", "maximum profit"]
BALANCED_PHRASES = ["medium risk", "balanced", "moderate", "medium"]
DIVIDEND_PHRASES = ["dividend", "income", "regular"]
SHORT_PHRASES = ["short term", "shortterm", "quick", "today"]
LONG_PHRASES = ["long term", "longterm", "future", "years", "retire"]

SECTOR_WORDS = {
    "IT": ["tech", "technology", "software", "it sector", "it stock", "it company"],
    "Banking": ["banking", "finance", "financial"],
    "Energy": ["energy", "power", "renewable"],
    "Pharma": ["pharma", "medicine", "medical", "health", "healthcare"],
    "Auto": ["auto", "car", "motors", "vehicle"],
    "FMCG": ["fmcg", "food", "grocery", "consumer"],
    "Real Estate": ["realty", "property", "estate", "housing"],
    "Metals": ["metal", "gold"],
}

STYLE_WEIGHTS = {
    "safe": {"mom": 0.5, "stab": 2.0, "div": 1.0, "chg": 0.3, "bump": 0.0,
             "risk": {"Low": 1.0, "Medium": 0.3, "High": -0.6}},
    "balanced": {"mom": 1.0, "stab": 1.0, "div": 0.6, "chg": 0.5, "bump": 0.0,
                 "risk": {"Low": 0.3, "Medium": 0.3, "High": 0.0}},
    "growth": {"mom": 1.5, "stab": 0.0, "div": 0.1, "chg": 0.8, "bump": 1.4,
               "risk": {"Low": -0.4, "Medium": 0.2, "High": 0.8}},
}
STYLE_NAMES = {"safe": "a safe and steady style", "balanced": "a balanced style",
               "growth": "a faster growth style (more risk)"}

DISCLAIMER = ("Remember: this is a practice market with made-up companies and simulated "
              "prices, so it is for learning, not real investment advice.")

SUGGESTIONS = ("Try asking:\n"
               "- How do I transfer money?\n"
               "- Which stock should I buy?\n"
               "- Show me safe stocks\n"
               "- Tell me about TCNX\n"
               "- Compare TCNX and FINB\n"
               "- How is the market today?\n"
               "- What is my portfolio?")


class Chatbot:
    # A rule based assistant: it matches your words to topics, then answers using
    # the live practice market and your account data. It does not need internet.

    def __init__(self, market):
        self.market = market
        self.last_intent = None
        self.last_prefs = None
        self.last_symbol = None

    # ------------------------------------------------------------------
    def reply(self, text, acc_no):
        raw = text.strip()
        if raw == "":
            return "Type a question and I will try to help."
        lower = raw.lower().replace("'", "")
        words = set(tokenize(lower))
        howto = re.search(r"\bhow (do|can|could|should|to|would)\b|\bsteps?\b|\bguide\b"
                          r"|\bkaise\b|\bkese\b|\bwhere\b", lower) is not None

        # small talk
        if (words & {"hi", "hello", "hey", "hii", "namaste", "hlo"} and len(words) <= 6) or \
                ("good" in words and words & {"morning", "afternoon", "evening", "night"}):
            return self.greeting(acc_no)
        if re.search(r"how are you|how r u|whats up", lower):
            return "I'm doing well, thanks for asking! What would you like to know?"
        if words & {"thanks", "thank", "thx", "shukriya", "dhanyavad"}:
            return "You're welcome! Ask me anything else about AR Bank or the stock market."
        if words & {"bye", "goodbye"}:
            return "Bye! Come back whenever you need help."
        if re.search(r"who are you|your name|are you (an )?(ai|bot|real|human)|what are you"
                     r"|chatgpt|do you need internet|are you online", lower):
            return ("I'm AR Assistant, a rule based chatbot built into this app. I match "
                    "your words to topics and use the live practice-market numbers and "
                    "your own account data to answer. I'm not a big AI model, and I run "
                    "fully on this computer without internet.")
        if "help" in words or re.search(r"what can you do|what do you do|your features", lower):
            return self.capabilities()
        if re.search(r"\b(buy|sell)\b.*\bfor me\b|\bfor me\b.*\b(buy|sell)\b", lower):
            return ("I can't place trades for you. Open the 'Stocks' page, pick a company, "
                    "type the number of shares and click Buy or Sell. I can help you decide, "
                    "though. Ask me 'which stock should I buy?'.")

        # explanations of a word, e.g. "what is a dividend"
        asking_meaning = re.search(r"\bwhat (is|are|does)\b|\bwhats\b|\bexplain\b|\bmeaning\b"
                                   r"|\bdefine\b|\bdefinition\b", lower) is not None
        found = self.find_stocks(lower, words)
        if "why" in words and words & {"price", "move", "moving", "change", "changing"} and not found:
            return self.concept_for({"simulation"})
        if asking_meaning and not (words & RECOMMEND_WORDS) and not found and "my" not in words:
            answer = self.concept_for(words)
            if answer:
                return answer

        # how-to questions about the app
        if howto:
            guide = find_guide(words)
            if guide:
                self.last_intent = "guide"
                return guide

        # follow-up: "why did you pick those?"
        if "why" in words and self.last_intent == "recommend":
            return self.explain_scoring()

        # stocks mentioned by name
        if len(found) >= 2:
            return self.compare(found[:2], acc_no)
        if len(found) == 1:
            self.last_symbol = found[0]
            self.last_intent = "stock"
            return self.about_stock(found[0], acc_no, words)

        # the user's own money
        if "my" in words or "mera" in words or "mere" in words:
            if words & {"portfolio", "holding", "stock", "share", "profit", "loss", "investment"}:
                return self.my_portfolio(acc_no)
            if words & {"balance", "money", "cash", "paisa", "paise"}:
                return self.my_balance(acc_no)
        if re.search(r"how much (money|cash)", lower) and "have" in words:
            return self.my_balance(acc_no)

        prefs = self.read_prefs(lower, words)
        mentions_stock = bool(words & {"stock", "share", "equity", "invest", "investment"})
        asks_pick = bool(words & {"recommend", "suggest", "best", "top", "pick", "kaunsa",
                                  "konsa", "invest", "investing", "investment"}
                         or ("which" in words and mentions_stock)
                         or ("what" in words and "buy" in words)
                         or ("should" in words and "buy" in words)
                         or re.search(r"good (stock|share)|stock to buy|worth buying", lower))

        # market overview
        if words & {"gainer", "loser", "trending", "index", "nifty", "sensex"} or (
                not asks_pick and (
                    re.search(r"how is the market|market today|market now|market trend", lower)
                    or "market" in words)):
            return self.market_summary()

        # stock recommendation
        has_pref = prefs["style"] is not None or prefs["sector"] or prefs["focus"] or prefs["horizon"]
        follow_up = self.last_intent == "recommend" and re.search(
            r"what about|how about|instead|\bones\b|\bbut\b|\balso\b|\bmore\b", lower)
        if asks_pick or (mentions_stock and has_pref) or (follow_up and has_pref):
            amount = None
            number = re.search(r"\b(\d{3,})\b", lower.replace(",", ""))
            if number:
                amount = float(number.group(1))
            return self.recommend(prefs, acc_no, amount, keep_old=bool(follow_up))

        # plain topic words without "how", e.g. just "deposit"
        guide = find_guide(words)
        if guide:
            self.last_intent = "guide"
            return guide

        concept = self.concept_for(words) if asking_meaning else None
        if concept:
            return concept

        return ("Sorry, I did not understand that. I can explain how to use AR Bank, show "
                "your balance and portfolio, and look at the live practice market.\n\n"
                + SUGGESTIONS)

    # ------------------------------------------------------------------
    def greeting(self, acc_no):
        acc = db.get_account(acc_no)
        name = acc["name"] if acc else "there"
        return (f"Hello {name}! I can show you how to use AR Bank, tell you about your "
                f"balance and stocks, and suggest which practice stocks to look at.\n\n"
                + SUGGESTIONS)

    def capabilities(self):
        return ("I can help with:\n"
                "- How to use AR Bank: create account, deposit, withdraw, transfer, statement, "
                "PIN problems, buying and selling stocks\n"
                "- Your own numbers: balance and stock portfolio\n"
                "- The live practice market: gainers, losers, one company in detail, "
                "comparing two companies\n"
                "- Which stock to look at: tell me safe, risky, dividend, short term, "
                "long term or a sector like 'IT stocks'\n"
                "- Meanings of words like dividend, risk, diversification\n\n"
                + SUGGESTIONS)

    def concept_for(self, words):
        for keys, answer in CONCEPTS:
            if any(k in words for k in keys):
                return answer
        return None

    # ------------------------------------------------------------------
    def find_stocks(self, lower, words):
        found = []
        for symbol, stock in self.market.stocks.items():
            first_word = stock["name"].split()[0].lower()
            if symbol.lower() in words or first_word in words or stock["name"].lower() in lower:
                found.append(symbol)
        return found

    def swing_word(self, vol):
        if vol < 0.15:
            return "steady"
        if vol < 0.23:
            return "moderate"
        return "very bumpy"

    def owned_line(self, symbol, acc_no):
        for h in db.get_holdings(acc_no):
            if h["symbol"] == symbol:
                price = self.market.price(symbol)
                profit = (price - h["avg_price"]) * h["qty"]
                return (f"You own {h['qty']} share(s) bought at an average of "
                        f"{money(h['avg_price'])}. Right now that is {profit:+,.2f} "
                        f"profit / loss.", h)
        return None, None

    def about_stock(self, symbol, acc_no, words):
        m = self.market
        stock = m.stocks[symbol]
        price = stock["price"]
        mom = m.momentum(symbol, 60)
        chg = m.change_pct(symbol)
        vol = m.volatility(symbol)

        lines = [f"{stock['name']} ({symbol}) - {stock['sector']}, {stock['risk'].lower()} risk",
                 f"Price now: {money(price)}",
                 f"Since the market opened: {chg:+.2f}%  |  last minute: {mom:+.2f}%",
                 f"Price swings: {self.swing_word(vol)}  |  dividend about {stock['dividend']}%"]
        owned, holding = self.owned_line(symbol, acc_no)
        if owned:
            lines.append(owned)
        lines.append("")

        if "sell" in words and holding:
            lines.append("If you sell now you lock in the profit or loss shown above. Selling "
                         "makes sense if you need the cash or you think it will keep falling. "
                         "Otherwise holding is fine.")
        else:
            if mom > 0.3 and vol < 0.23:
                lines.append("What the numbers say: it is rising and its price is not too bumpy, "
                             "so buying a few shares looks reasonable.")
            elif mom > 0.3:
                lines.append("What the numbers say: it is rising, but the price swings a lot, "
                             "so buy only a small amount.")
            elif mom < -0.3:
                lines.append("What the numbers say: it is falling lately. You could wait to see "
                             "if it settles, or buy only a little.")
            else:
                lines.append("What the numbers say: the price is flat right now, so there is no "
                             "hurry either way.")
            if stock["risk"] == "High":
                lines.append("It is a high risk company, so keep it a small part of your money.")
            acc = db.get_account(acc_no)
            if acc and price > 0:
                can = int(acc["balance"] // price)
                if can >= 1:
                    lines.append(f"With your cash of {money(acc['balance'])} you could buy up to "
                                 f"{can} share(s).")
                else:
                    lines.append("Your cash is not enough for one share yet. Deposit money first.")
        lines.append("")
        lines.append(DISCLAIMER)
        return "\n".join(lines)

    def compare(self, pair, acc_no):
        m = self.market
        a, b = pair
        sa, sb = m.stocks[a], m.stocks[b]
        rows = [
            ("Company", sa["name"], sb["name"]),
            ("Sector / risk", f"{sa['sector']} / {sa['risk']}", f"{sb['sector']} / {sb['risk']}"),
            ("Price", money(sa["price"]), money(sb["price"])),
            ("Since open", f"{m.change_pct(a):+.2f}%", f"{m.change_pct(b):+.2f}%"),
            ("Last minute", f"{m.momentum(a, 60):+.2f}%", f"{m.momentum(b, 60):+.2f}%"),
            ("Price swings", self.swing_word(m.volatility(a)), self.swing_word(m.volatility(b))),
            ("Dividend", f"{sa['dividend']}%", f"{sb['dividend']}%"),
        ]
        lines = [f"{a} vs {b}"]
        for label, x, y in rows:
            lines.append(f"- {label}: {x}  |  {y}")
        steadier = a if m.volatility(a) < m.volatility(b) else b
        livelier = b if steadier == a else a
        rising = a if m.momentum(a, 60) > m.momentum(b, 60) else b
        lines.append("")
        lines.append(f"{steadier} has been the steadier one, so it suits a careful style. "
                     f"{livelier} moves more, which can mean bigger gains but also bigger falls. "
                     f"{rising} has the better last minute.")
        lines.append("")
        lines.append(DISCLAIMER)
        self.last_symbol = a
        self.last_intent = "compare"
        return "\n".join(lines)

    # ------------------------------------------------------------------
    def my_balance(self, acc_no):
        acc = db.get_account(acc_no)
        if acc is None:
            return "I could not find your account."
        stocks_value = sum(self.market.price(h["symbol"]) * h["qty"]
                           for h in db.get_holdings(acc_no))
        text = f"Your available balance is {money(acc['balance'])}."
        if stocks_value > 0:
            text += (f" Your stocks are worth {money(stocks_value)} right now, so together "
                     f"you have {money(acc['balance'] + stocks_value)}.")
        return text

    def my_portfolio(self, acc_no):
        holdings = db.get_holdings(acc_no)
        if not holdings:
            return ("You do not own any stocks yet. Open the 'Stocks' page, or ask me "
                    "'which stock should I buy?' for ideas.")
        lines = ["Your portfolio right now:"]
        total_value = 0
        total_cost = 0
        biggest = None
        for h in holdings:
            price = self.market.price(h["symbol"])
            value = price * h["qty"]
            cost = h["avg_price"] * h["qty"]
            total_value += value
            total_cost += cost
            if biggest is None or value > biggest[1]:
                biggest = (h["symbol"], value)
            lines.append(f"- {h['symbol']}: {h['qty']} share(s), bought at {money(h['avg_price'])}, "
                         f"now {money(price)}, {value - cost:+,.2f} profit / loss")
        lines.append("")
        lines.append(f"Total value {money(total_value)}, profit / loss {total_value - total_cost:+,.2f}.")
        share = biggest[1] / total_value * 100
        if len(holdings) == 1:
            lines.append("All your stock money is in one company. Spreading it across 2 or 3 "
                         "companies lowers your risk.")
        elif share > 60:
            lines.append(f"{biggest[0]} is {share:.0f}% of your portfolio. That is a lot in one "
                         f"company, so consider spreading it out.")
        return "\n".join(lines)

    def market_summary(self):
        m = self.market
        change = m.index_change()
        mood = "up" if change > 0.15 else "down" if change < -0.15 else "almost flat"
        ranked = sorted(m.symbols(), key=lambda s: m.change_pct(s), reverse=True)
        gainers = ", ".join(f"{s} ({m.change_pct(s):+.2f}%)" for s in ranked[:3])
        losers = ", ".join(f"{s} ({m.change_pct(s):+.2f}%)" for s in ranked[::-1][:3])
        by_vol = sorted(m.symbols(), key=lambda s: m.volatility(s))
        self.last_intent = "market"
        return (f"The AR Index is {m.index_value():,.2f} ({change:+.2f}% since open), so the "
                f"market is {mood}.\n"
                f"- Top gainers: {gainers}\n"
                f"- Biggest fallers: {losers}\n"
                f"- Steadiest price: {by_vol[0]}, bumpiest: {by_vol[-1]}\n\n"
                "Ask 'which stock should I buy?' if you want ideas.")

    # ------------------------------------------------------------------
    def read_prefs(self, lower, words):
        def found(phrases):
            return any(re.search(r"\b" + re.escape(p) + r"s?\b", lower) for p in phrases)

        prefs = {"style": None, "sector": None, "focus": None, "horizon": None}
        if found(SAFE_PHRASES):
            prefs["style"] = "safe"
        elif found(GROWTH_PHRASES):
            prefs["style"] = "growth"
        elif found(BALANCED_PHRASES):
            prefs["style"] = "balanced"
        if found(DIVIDEND_PHRASES):
            prefs["focus"] = "dividend"
        if found(SHORT_PHRASES):
            prefs["horizon"] = "short"
        elif found(LONG_PHRASES):
            prefs["horizon"] = "long"
        for sector, keys in SECTOR_WORDS.items():
            if found(keys):
                prefs["sector"] = sector
        return prefs

    def score(self, symbol, prefs):
        m = self.market
        stock = m.stocks[symbol]
        w = dict(STYLE_WEIGHTS[prefs["style"] or "balanced"])
        if prefs["focus"] == "dividend":
            w["div"] += 4.0
        if prefs["horizon"] == "long":
            w["stab"] += 0.5
            w["div"] += 0.5
            w["mom"] *= 0.5
        elif prefs["horizon"] == "short":
            w["mom"] += 0.8
        mom = max(-2, min(2, m.momentum(symbol, 60))) / 2
        chg = max(-3, min(3, m.change_pct(symbol))) / 3
        stab = 1 - min(m.volatility(symbol) / 0.35, 1)
        div = stock["dividend"] / 2.1
        return (w["mom"] * mom + w["stab"] * stab + w["div"] * div + w["chg"] * chg
                + w["bump"] * (1 - stab) + w["risk"][stock["risk"]])

    def reasons(self, symbol, prefs):
        m = self.market
        stock = m.stocks[symbol]
        vol = m.volatility(symbol)
        mom = m.momentum(symbol, 60)
        out = []
        if stock["risk"] == "Low":
            out.append("low risk company")
        if vol < 0.15:
            out.append("very steady price")
        elif vol > 0.23:
            out.append("price swings a lot")
        if mom > 0.3:
            out.append(f"up {mom:.2f}% in the last minute")
        elif mom < -0.3:
            out.append(f"down {abs(mom):.2f}% in the last minute")
        if stock["dividend"] >= 1.2 or prefs["focus"] == "dividend":
            out.append(f"dividend about {stock['dividend']}%")
        return out or ["balanced numbers right now"]

    def recommend(self, prefs, acc_no, amount=None, keep_old=False):
        # a follow-up like "what about safer ones" keeps the old wishes
        if keep_old and self.last_prefs:
            for key, value in self.last_prefs.items():
                if prefs[key] is None:
                    prefs[key] = value
        self.last_prefs = dict(prefs)
        self.last_intent = "recommend"

        m = self.market
        symbols = m.symbols()
        if prefs["sector"]:
            symbols = [s for s in symbols if m.stocks[s]["sector"] == prefs["sector"]]
        if prefs["style"] == "growth":
            bolder = [s for s in symbols if m.stocks[s]["risk"] != "Low"]
            symbols = bolder or symbols
        ranked = sorted(symbols, key=lambda s: self.score(s, prefs), reverse=True)[:3]

        style = prefs["style"] or "balanced"
        head = f"Based on the live practice market right now, for {STYLE_NAMES[style]}"
        if prefs["sector"]:
            head += f" in {prefs['sector']}"
        if prefs["focus"] == "dividend":
            head += " with good dividends"
        if prefs["horizon"]:
            head += f" ({prefs['horizon']} term)"
        lines = [head + ", I would look at:", ""]
        for i, symbol in enumerate(ranked, start=1):
            stock = m.stocks[symbol]
            lines.append(f"{i}. {symbol} - {stock['name']} ({stock['sector']}, {stock['risk']} risk)")
            lines.append(f"   {money(stock['price'])}  -  " + ", ".join(self.reasons(symbol, prefs)))
        self.last_symbol = ranked[0]

        acc = db.get_account(acc_no)
        lines.append("")
        if amount and acc:
            if amount > acc["balance"]:
                lines.append(f"Note: {money(amount)} is more than the cash in your account "
                             f"({money(acc['balance'])}). Deposit first, or use a smaller amount.")
            part = amount / len(ranked)
            plan = []
            for symbol in ranked:
                shares = int(part // m.price(symbol))
                plan.append(f"{shares} share(s) of {symbol}")
            lines.append(f"If you invest {money(amount)} and split it evenly, that is about "
                         + ", ".join(plan) + ". Splitting lowers your risk.")
        elif acc:
            top_price = m.price(ranked[0])
            can = int(acc["balance"] // top_price)
            if can >= 1:
                lines.append(f"With your cash of {money(acc['balance'])} you could buy up to {can} "
                             f"share(s) of {ranked[0]}. Don't put everything in one stock. "
                             f"Spreading across 2 or 3 companies lowers your risk.")
            else:
                lines.append(f"Your cash ({money(acc['balance'])}) is not enough for one share of "
                             f"{ranked[0]} yet. Deposit money first.")
        lines.append("Tell me 'safe', 'risky', 'dividend', 'long term' or a sector like "
                     "'IT stocks' and I will adjust. Ask 'why' to see how I chose.")
        lines.append("")
        lines.append(DISCLAIMER)
        return "\n".join(lines)

    def explain_scoring(self):
        return ("I score every company using the live numbers:\n"
                "- how steady its price has been (less jumping = higher score)\n"
                "- how it moved in the last minute and since the market opened\n"
                "- its dividend\n"
                "- its risk label (Low, Medium, High)\n"
                "For a 'safe' wish I give steadiness and low risk the most weight. For "
                "'growth' I give recent upward movement the most weight and accept bigger "
                "swings. Then I show the top 3. Because prices move every second, the "
                "ranking can change when you ask again.")