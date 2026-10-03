import tkinter as tk
from tkinter import ttk, messagebox
import database as db
from ui import (BG, SURFACE, BORDER, TEXT, MUTED, ACCENT, RED, FONT,
                make_button, make_entry)

UP_FILL = "#d1fae5"
DOWN_FILL = "#fee2e2"


def arrow(value):
    return "▲" if value >= 0 else "▼"


class StockPage:
    # the stock market screen: watchlist, live graph, buy/sell and portfolio

    def __init__(self, app):
        self.app = app
        self.market = app.market
        self.selected = self.market.symbols()[0]
        self.build()
        self.refresh()

    # ---------------- building the screen ----------------
    def build(self):
        self.root = tk.Frame(self.app.content, bg=BG)
        self.root.pack(fill="both", expand=True)
        self.root.grid_columnconfigure(0, weight=2, uniform="cols")
        self.root.grid_columnconfigure(1, weight=3, uniform="cols")
        self.root.grid_rowconfigure(1, weight=3)
        self.root.grid_rowconfigure(2, weight=2)

        # top row: title and the market index
        header = tk.Frame(self.root, bg=BG)
        header.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 16))
        title = tk.Frame(header, bg=BG)
        title.pack(side="left")
        tk.Label(title, text="Stock market", bg=BG, fg=TEXT,
                 font=(FONT, 26, "bold")).pack(anchor="w")
        tk.Label(title, text="Practice market with simulated prices. Works fully offline.",
                 bg=BG, fg=MUTED, font=(FONT, 12)).pack(anchor="w")

        index_box = tk.Frame(header, bg=SURFACE, padx=22, pady=12)
        index_box.pack(side="right")
        self.index_label = tk.Label(index_box, text="", bg=SURFACE, fg=TEXT,
                                    font=(FONT, 16, "bold"))
        self.index_label.pack(side="left")
        self.index_change = tk.Label(index_box, text="", bg=SURFACE,
                                     font=(FONT, 12, "bold"))
        self.index_change.pack(side="left", padx=(12, 14))
        tk.Label(index_box, text="● LIVE", bg=SURFACE, fg=ACCENT,
                 font=(FONT, 10, "bold")).pack(side="left")

        # left: market watch
        watch_box = tk.Frame(self.root, bg=BG)
        watch_box.grid(row=1, column=0, sticky="nsew", padx=(0, 20))
        tk.Label(watch_box, text="Market watch", bg=BG, fg=TEXT,
                 font=(FONT, 14, "bold")).pack(anchor="w", pady=(0, 8))
        columns = ("Symbol", "Company", "Price", "Change")
        self.watch = ttk.Treeview(watch_box, columns=columns, show="headings",
                                  height=8, selectmode="browse")
        widths = {"Symbol": 70, "Company": 170, "Price": 90, "Change": 100}
        for col in columns:
            self.watch.heading(col, text=col)
            self.watch.column(col, width=widths[col], anchor="center")
        self.watch.column("Company", anchor="w")
        self.watch.tag_configure("up", foreground=ACCENT)
        self.watch.tag_configure("down", foreground=RED)
        for symbol in self.market.symbols():
            name = self.market.stocks[symbol]["name"]
            self.watch.insert("", "end", iid=symbol, values=(symbol, name, "", ""))
        self.watch.pack(fill="both", expand=True)
        self.watch.selection_set(self.selected)
        self.watch.bind("<<TreeviewSelect>>", self.on_pick)

        # right: graph and the buy / sell box
        right = tk.Frame(self.root, bg=BG)
        right.grid(row=1, column=1, sticky="nsew")
        self.chart = tk.Canvas(right, bg="white", height=280, highlightthickness=1,
                               highlightbackground=BORDER)
        self.chart.pack(fill="both", expand=True)
        self.chart.bind("<Configure>", lambda e: self.draw_chart())

        trade = tk.Frame(right, bg=SURFACE, padx=22, pady=14)
        trade.pack(fill="x", pady=(12, 0))
        self.trade_info = tk.Label(trade, text="", bg=SURFACE, fg=MUTED,
                                   font=(FONT, 10), justify="left", anchor="w")
        self.trade_info.pack(side="left")
        controls = tk.Frame(trade, bg=SURFACE)
        controls.pack(side="right")
        tk.Label(controls, text="Shares", bg=SURFACE, fg=MUTED,
                 font=(FONT, 10)).pack(side="left", padx=(0, 8))
        self.qty_entry = make_entry(controls)
        self.qty_entry.config(width=8)
        self.qty_entry.insert(0, "1")
        self.qty_entry.pack(side="left", ipady=6)
        make_button(controls, "Buy", lambda: self.trade_stock("buy")).pack(
            side="left", padx=(12, 6))
        make_button(controls, "Sell", lambda: self.trade_stock("sell"),
                    "danger").pack(side="left")

        # bottom: your portfolio
        port = tk.Frame(self.root, bg=BG)
        port.grid(row=2, column=0, columnspan=2, sticky="nsew", pady=(20, 0))
        top = tk.Frame(port, bg=BG)
        top.pack(fill="x", pady=(0, 8))
        tk.Label(top, text="Your portfolio", bg=BG, fg=TEXT,
                 font=(FONT, 14, "bold")).pack(side="left")
        self.summary = tk.Label(top, text="", bg=BG, fg=MUTED, font=(FONT, 11))
        self.summary.pack(side="right")
        columns = ("Symbol", "Shares", "Avg price", "Current", "Value", "Profit / Loss")
        self.port_tree = ttk.Treeview(port, columns=columns, show="headings",
                                      height=4, selectmode="browse")
        for col in columns:
            self.port_tree.heading(col, text=col)
            self.port_tree.column(col, width=110, anchor="center")
        self.port_tree.tag_configure("up", foreground=ACCENT)
        self.port_tree.tag_configure("down", foreground=RED)
        self.port_tree.pack(fill="both", expand=True)
        self.port_tree.bind("<<TreeviewSelect>>", self.on_pick_holding)

    # ---------------- live updates ----------------
    def refresh(self):
        m = self.market
        index = m.index_value()
        change = m.index_change()
        self.index_label.config(text=f"AR Index  {index:,.2f}")
        self.index_change.config(text=f"{arrow(change)} {change:+.2f}%",
                                 fg=ACCENT if change >= 0 else RED)

        for symbol in m.symbols():
            stock = m.stocks[symbol]
            pct = m.change_pct(symbol)
            self.watch.item(symbol, tags=("up" if pct >= 0 else "down",),
                            values=(symbol, stock["name"], f"{stock['price']:,.2f}",
                                    f"{arrow(pct)} {pct:+.2f}%"))
        self.draw_chart()
        self.update_trade_info()
        self.update_portfolio()

    def draw_chart(self):
        c = self.chart
        c.delete("all")
        w = c.winfo_width()
        h = c.winfo_height()
        if w < 120 or h < 120:
            return
        stock = self.market.stocks[self.selected]
        prices = list(stock["history"])
        last = prices[-1]
        pct = self.market.change_pct(self.selected)
        up = pct >= 0
        color = ACCENT if up else RED

        # heading of the graph
        c.create_text(24, 18, anchor="nw", text=self.selected, fill=TEXT,
                      font=(FONT, 20, "bold"))
        c.create_text(24, 50, anchor="nw", fill=MUTED, font=(FONT, 10),
                      text=f"{stock['name']}  ·  {stock['sector']}  ·  {stock['risk']} risk")
        c.create_text(w - 24, 18, anchor="ne", text=f"Rs. {last:,.2f}", fill=TEXT,
                      font=(FONT, 20, "bold"))
        c.create_text(w - 24, 50, anchor="ne", fill=color, font=(FONT, 10, "bold"),
                      text=f"{arrow(pct)} {pct:+.2f}% since open")

        # drawing area
        left, right, top, bottom = 80, w - 24, 90, h - 32
        low = min(min(prices), stock["open"])
        high = max(max(prices), stock["open"])
        pad = max((high - low) * 0.12, last * 0.001)
        low -= pad
        high += pad

        def y_of(price):
            return bottom - (price - low) / (high - low) * (bottom - top)

        def x_of(i):
            return left + i / (len(prices) - 1) * (right - left)

        for k in range(5):  # light grid lines with price labels
            gy = top + k * (bottom - top) / 4
            label = high - k * (high - low) / 4
            c.create_line(left, gy, right, gy, fill="#eef0f3")
            c.create_text(left - 10, gy, anchor="e", text=f"{label:,.2f}",
                          fill=MUTED, font=(FONT, 9))

        open_y = y_of(stock["open"])  # dashed line = price at the start
        c.create_line(left, open_y, right, open_y, fill="#9ca3af", dash=(4, 4))

        points = []
        for i, price in enumerate(prices):
            points += [x_of(i), y_of(price)]
        c.create_polygon([left, bottom] + points + [right, bottom],
                         fill=UP_FILL if up else DOWN_FILL, outline="")
        c.create_line(points, fill=color, width=2)

        end_x, end_y = x_of(len(prices) - 1), y_of(last)  # dot at the latest price
        c.create_oval(end_x - 5, end_y - 5, end_x + 5, end_y + 5, fill=color,
                      outline="white", width=2)
        c.create_text(left, bottom + 8, anchor="nw", text="2 min ago", fill=MUTED,
                      font=(FONT, 9))
        c.create_text(right, bottom + 8, anchor="ne", text="now", fill=MUTED,
                      font=(FONT, 9))

    def update_trade_info(self):
        stock = self.market.stocks[self.selected]
        acc = db.get_account(self.app.current_acc)
        owned = "You do not own this stock yet"
        for h in db.get_holdings(self.app.current_acc):
            if h["symbol"] == self.selected:
                owned = (f"You own {h['qty']} share(s), "
                         f"average cost Rs. {h['avg_price']:,.2f}")
        self.trade_info.config(
            text=f"{stock['name']} ({self.selected})\n{owned}\n"
                 f"Cash in your account: Rs. {acc['balance']:,.2f}")

    def update_portfolio(self):
        self.port_tree.delete(*self.port_tree.get_children())
        invested = 0
        current = 0
        for h in db.get_holdings(self.app.current_acc):
            price = self.market.price(h["symbol"])
            cost = h["avg_price"] * h["qty"]
            value = price * h["qty"]
            profit = value - cost
            pct = profit / cost * 100 if cost else 0
            invested += cost
            current += value
            self.port_tree.insert(
                "", "end", iid=h["symbol"], tags=("up" if profit >= 0 else "down",),
                values=(h["symbol"], h["qty"], f"{h['avg_price']:,.2f}",
                        f"{price:,.2f}", f"{value:,.2f}",
                        f"{profit:+,.2f} ({pct:+.2f}%)"))
        if invested == 0:
            self.summary.config(text="No stocks yet. Pick one above and click Buy.")
        else:
            total = current - invested
            self.summary.config(
                text=f"Invested Rs. {invested:,.2f}     Current Rs. {current:,.2f}"
                     f"     Profit / Loss {total:+,.2f}")

    # ---------------- clicks ----------------
    def on_pick(self, event=None):
        picked = self.watch.selection()
        if picked:
            self.selected = picked[0]
            self.draw_chart()
            self.update_trade_info()

    def on_pick_holding(self, event=None):
        picked = self.port_tree.selection()
        if picked:
            self.watch.selection_set(picked[0])  # this also calls on_pick

    def trade_stock(self, side):
        text = self.qty_entry.get().strip()
        if not text.isdigit() or int(text) < 1:
            messagebox.showerror("Error", "Enter the number of shares as a whole number")
            return
        qty = int(text)
        symbol = self.selected
        price = self.market.price(symbol)  # price at this moment
        total = round(qty * price, 2)
        word = "Buy" if side == "buy" else "Sell"
        sure = messagebox.askyesno(
            f"Confirm {word.lower()}",
            f"{word} {qty} share(s) of {symbol} at Rs. {price:,.2f}?\n"
            f"Total: Rs. {total:,.2f}")
        if not sure:
            return
        if side == "buy":
            ok, msg = db.buy_stock(self.app.current_acc, symbol, qty, price)
        else:
            ok, msg = db.sell_stock(self.app.current_acc, symbol, qty, price)
        if ok:
            messagebox.showinfo("Done", msg)
        else:
            messagebox.showerror("Error", msg)
        self.refresh()