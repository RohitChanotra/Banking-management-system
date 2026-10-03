import math
import time
import tkinter as tk
from datetime import datetime
from tkinter import messagebox, ttk, simpledialog

import database as db
import assistant_page
import stock_page
import ui
from market import Market
from ui import (BG, SURFACE, TINT, SKY, BORDER, TEXT, MUTED, ACCENT, RED, FONT,
                make_button, make_entry, with_loading, draw_bill, brand_mark,
                draw_scene)

# ---------- loading animation settings ----------
LOADING_SECONDS = 1.0
LANES = [0.18, 0.30, 0.42, 0.54, 0.66, 0.78]    # how high up each note flies
SPEEDS = [1.0, 1.25, 0.9, 1.15, 1.05, 1.3]
PHASES = [0.0, 0.3, 0.6, 0.15, 0.8, 0.45]


class BankApp(tk.Tk):
    def __init__(self):
        super().__init__()
        ui.APP = self  # buttons in ui.py use this to start the animation
        self.title("AR Bank")
        self.configure(bg=BG)
        self.geometry("1200x720")
        self.minsize(1000, 650)
        try:
            self.state("zoomed")  # open maximized
        except tk.TclError:
            pass

        self.setup_styles()
        self.current_acc = None
        self.loading = False
        self.active_page = None
        self.nav_buttons = {}
        self.stock_page = None
        self.market = Market()  # the practice stock market (runs offline)

        self.container = tk.Frame(self, bg=BG)
        self.container.pack(fill="both", expand=True)
        # this canvas covers the whole window while the animation plays
        self.overlay = tk.Canvas(self, bg=BG, highlightthickness=0)
        self.show_login()
        self.tick_market()

    # ---------------- look of the tables ----------------
    def setup_styles(self):
        style = ttk.Style()
        style.theme_use("clam")
        style.layout("Treeview", [("Treeview.treearea", {"sticky": "nswe"})])
        style.configure("Treeview", background=BG, fieldbackground=BG,
                        foreground=TEXT, rowheight=36, borderwidth=0,
                        font=(FONT, 11))
        style.configure("Treeview.Heading", background=SURFACE, foreground=MUTED,
                        font=(FONT, 10, "bold"), relief="flat", padding=8)
        style.map("Treeview", background=[("selected", "#d1fae5")],
                  foreground=[("selected", TEXT)])
        style.map("Treeview.Heading", background=[("active", SURFACE)])

    # ---------------- live stock prices ----------------
    def tick_market(self):
        self.after(1000, self.tick_market)  # run again after 1 second
        self.market.tick()
        if self.stock_page is not None and self.active_page == "Stocks":
            try:
                self.stock_page.refresh()
            except tk.TclError:
                pass  # the page was closed at the same moment

    # ---------------- loading animation ----------------
    def run_with_loading(self, command):
        if self.loading:
            return
        self.loading = True
        self.update_idletasks()
        self.overlay.place(x=0, y=0, relwidth=1, relheight=1)
        tk.Misc.tkraise(self.overlay)
        self.anim_start = time.time()
        self.anim_command = command
        self.animate()

    def animate(self):
        t = (time.time() - self.anim_start) / LOADING_SECONDS
        if t >= 1:
            # animation finished: hide it and do what the button was meant to do
            self.overlay.place_forget()
            self.loading = False
            self.anim_command()
            return

        w = self.winfo_width()
        h = self.winfo_height()
        canvas = self.overlay
        canvas.delete("all")
        canvas.create_text(w // 2, h // 2, text="Please wait...", fill=MUTED,
                           font=(FONT, 16))
        for i in range(len(LANES)):
            p = (t * SPEEDS[i] + PHASES[i]) % 1
            x = -130 + (w + 260) * p
            y = h * LANES[i] + math.sin(p * 14 + i) * 20
            flap_up = int(t * 14 + i) % 2 == 0
            draw_bill(canvas, x, y, flap_up)
        self.after(35, self.animate)

    # ---------------- helpers ----------------
    def clear(self):
        # remove everything on screen before showing a new page
        for widget in self.container.winfo_children():
            widget.destroy()

    def field(self, parent, label, show=None):
        bg = parent.cget("bg")
        tk.Label(parent, text=label, bg=bg, fg=MUTED,
                 font=(FONT, 10)).pack(anchor="w", pady=(12, 4))
        entry = make_entry(parent, show)
        entry.pack(fill="x", ipady=7)
        return entry

    def auth_layout(self, title, subtitle):
        # split page used by login, create account and admin login
        self.clear()
        left = tk.Frame(self.container, bg=TINT)
        left.place(relx=0, rely=0, relwidth=0.42, relheight=1)
        inner = tk.Frame(left, bg=TINT)
        inner.place(relx=0.5, rely=0.5, anchor="center")
        brand_mark(inner, TINT).pack()
        tk.Label(inner, text="AR Bank", bg=TINT, fg=TEXT,
                 font=(FONT, 40, "bold")).pack(pady=(10, 0))
        tk.Label(inner, text="Simple. Secure. Yours.", bg=TINT, fg=MUTED,
                 font=(FONT, 14)).pack()

        right = tk.Frame(self.container, bg=BG)
        right.place(relx=0.42, rely=0, relwidth=0.58, relheight=1)
        form = tk.Frame(right, bg=BG)
        form.place(relx=0.5, rely=0.5, anchor="center")
        tk.Label(form, text=title, bg=BG, fg=TEXT,
                 font=(FONT, 26, "bold")).pack(anchor="w")
        tk.Label(form, text=subtitle, bg=BG, fg=MUTED,
                 font=(FONT, 11)).pack(anchor="w", pady=(2, 10))
        return form

    # ---------------- login page ----------------
    def show_login(self):
        self.current_acc = None
        self.stock_page = None
        self.active_page = None
        form = self.auth_layout("Welcome back", "Sign in to your account")
        self.acc_entry = self.field(form, "Account number")
        self.pin_entry = self.field(form, "PIN", show="•")

        make_button(form, "Login", self.do_login).pack(fill="x", pady=(26, 8))
        make_button(form, "Create new account", self.show_create,
                    "secondary").pack(fill="x", pady=(0, 8))
        make_button(form, "Admin login", self.show_admin_login,
                    "secondary").pack(fill="x")

    def do_login(self):
        acc_text = self.acc_entry.get().strip()
        pin = self.pin_entry.get().strip()
        if not acc_text.isdigit():
            messagebox.showerror("Error", "Please enter a valid account number")
            return
        ok, msg = db.login(int(acc_text), pin)
        if ok:
            self.current_acc = int(acc_text)
            self.show_dashboard()
        else:
            messagebox.showerror("Login failed", msg)

    # ---------------- create account page ----------------
    def show_create(self):
        form = self.auth_layout("Create account", "It only takes a minute")
        self.name_entry = self.field(form, "Full name")
        self.phone_entry = self.field(form, "Phone number")
        self.new_pin = self.field(form, "Choose a 4 digit PIN", show="•")
        self.confirm_pin = self.field(form, "Confirm PIN", show="•")

        make_button(form, "Create account", self.do_create).pack(fill="x", pady=(24, 8))
        make_button(form, "Back to login", self.show_login,
                    "secondary").pack(fill="x")

    def do_create(self):
        name = self.name_entry.get().strip()
        phone = self.phone_entry.get().strip()
        pin = self.new_pin.get().strip()
        confirm = self.confirm_pin.get().strip()

        if name == "":
            messagebox.showerror("Error", "Please enter your name")
            return
        if not phone.isdigit() or len(phone) != 10:
            messagebox.showerror("Error", "Phone number must be 10 digits")
            return
        if pin != confirm:
            messagebox.showerror("Error", "The two PINs do not match")
            return

        acc_no, msg = db.create_account(name, phone, pin)
        if acc_no is None:
            messagebox.showerror("Error", msg)
            return
        messagebox.showinfo("Success",
                            f"Account created!\nYour account number is {db.format_acc(acc_no)}")
        self.show_login()

    # ---------------- dashboard ----------------
    def show_dashboard(self):
        self.clear()
        self.nav_buttons = {}
        acc = db.get_account(self.current_acc)

        sidebar = tk.Frame(self.container, bg=SURFACE, width=260)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)
        tk.Frame(self.container, bg=BORDER, width=1).pack(side="left", fill="y")

        tk.Label(sidebar, text="AR Bank", bg=SURFACE, fg=TEXT,
                 font=(FONT, 20, "bold")).pack(pady=(34, 2))
        tk.Label(sidebar, text=acc["name"], bg=SURFACE, fg=MUTED,
                 font=(FONT, 11)).pack()
        tk.Label(sidebar, text=f"A/C {db.format_acc(acc['acc_no'])}", bg=SURFACE,
                 fg=MUTED, font=(FONT, 10)).pack(pady=(0, 30))

        menu = [("Home", self.show_home), ("Deposit", self.show_deposit),
                ("Withdraw", self.show_withdraw), ("Transfer", self.show_transfer),
                ("Stocks", self.show_stocks), ("Assistant", self.show_assistant),
                ("Statement", self.show_statement)]
        for text, command in menu:
            self.nav_button(sidebar, text, command)

        make_button(sidebar, "Logout", self.logout,
                    "secondary").pack(side="bottom", fill="x", padx=20, pady=25)

        self.content = tk.Frame(self.container, bg=BG, padx=55, pady=40)
        self.content.pack(side="left", fill="both", expand=True)
        self.show_home()

    def nav_button(self, parent, text, command):
        btn = tk.Button(parent, text=text, command=with_loading(command),
                        bg=SURFACE, fg=MUTED, font=(FONT, 12), relief="flat",
                        bd=0, anchor="w", padx=26, pady=12, cursor="hand2",
                        activebackground=TINT, activeforeground=ACCENT)
        btn.pack(fill="x", padx=14, pady=2)
        btn.bind("<Enter>", lambda e: btn.config(bg="#eceff3")
                 if self.active_page != text else None)
        btn.bind("<Leave>", lambda e: btn.config(bg=SURFACE)
                 if self.active_page != text else None)
        self.nav_buttons[text] = btn

    def set_active(self, name):
        # highlights the sidebar button of the page we are on
        self.active_page = name
        for text, btn in self.nav_buttons.items():
            if text == name:
                btn.config(bg=TINT, fg=ACCENT, font=(FONT, 12, "bold"))
            else:
                btn.config(bg=SURFACE, fg=MUTED, font=(FONT, 12))

    def logout(self):
        self.show_login()

    def clear_content(self):
        for widget in self.content.winfo_children():
            widget.destroy()
        self.stock_page = None

    def heading(self, text, sub=None):
        tk.Label(self.content, text=text, bg=BG, fg=TEXT,
                 font=(FONT, 26, "bold")).pack(anchor="w")
        if sub:
            tk.Label(self.content, text=sub, bg=BG, fg=MUTED,
                     font=(FONT, 12)).pack(anchor="w", pady=(2, 22))

    def form_card(self):
        card = tk.Frame(self.content, bg=SURFACE, padx=36, pady=30)
        card.pack(anchor="w")
        return card

    def read_amount(self):
        try:
            amount = float(self.amount_entry.get().strip())
        except ValueError:
            messagebox.showerror("Error", "Please enter a valid amount")
            return None
        return round(amount, 2)

    def make_table(self, rows, height=10):
        columns = ("Date", "Type", "Amount", "Balance", "Note")
        table = ttk.Treeview(self.content, columns=columns, show="headings",
                             height=height)
        for col in columns:
            table.heading(col, text=col)
            table.column(col, width=140, anchor="center")
        table.tag_configure("odd", background="#f9fafb")
        for i, r in enumerate(rows):
            money_in = r["type"] in ("Deposit", "Transfer In", "Stock Sell")
            sign = "+" if money_in else "-"
            table.insert("", "end", tags=("odd" if i % 2 else "even",),
                         values=(r["created_at"], r["type"],
                                 f"{sign}{r['amount']:.2f}",
                                 f"{r['balance_after']:.2f}", r["note"]))
        table.pack(fill="both", expand=True)

    # ----- home -----
    def show_home(self):
        self.set_active("Home")
        self.clear_content()
        acc = db.get_account(self.current_acc)

        # money in shares right now
        holdings = db.get_holdings(self.current_acc)
        invested = sum(h["avg_price"] * h["qty"] for h in holdings)
        current = sum(self.market.price(h["symbol"]) * h["qty"] for h in holdings)
        profit = current - invested

        # one big canvas: the pixel bank is drawn behind the text and cards
        canvas = tk.Canvas(self.content, bg=SKY, highlightthickness=0)
        canvas.place(x=0, y=0, relwidth=1, relheight=1)
        canvas.bind("<Configure>", lambda e: draw_scene(canvas, e.width, e.height))

        hour = datetime.now().hour
        if hour < 12:
            greeting = "Good morning"
        elif hour < 17:
            greeting = "Good afternoon"
        else:
            greeting = "Good evening"
        canvas.create_text(60, 50, anchor="nw", text=f"{greeting}, {acc['name']}",
                           fill=TEXT, font=(FONT, 30, "bold"))
        canvas.create_text(62, 102, anchor="nw",
                           text=f"Account {db.format_acc(acc['acc_no'])}",
                           fill=MUTED, font=(FONT, 12))

        # card 1: balance
        canvas.create_rectangle(60, 150, 400, 275, fill="white", outline=BORDER)
        canvas.create_text(84, 170, anchor="nw", text="Available balance",
                           fill=MUTED, font=(FONT, 11))
        canvas.create_text(84, 200, anchor="nw", text=f"Rs. {acc['balance']:,.2f}",
                           fill=TEXT, font=(FONT, 26, "bold"))

        # card 2: stock portfolio
        canvas.create_rectangle(420, 150, 760, 275, fill="white", outline=BORDER)
        canvas.create_text(444, 170, anchor="nw", text="Stock portfolio",
                           fill=MUTED, font=(FONT, 11))
        canvas.create_text(444, 200, anchor="nw", text=f"Rs. {current:,.2f}",
                           fill=TEXT, font=(FONT, 26, "bold"))
        if holdings:
            note = f"{profit:+,.2f} profit / loss"
            note_color = ACCENT if profit >= 0 else RED
        else:
            note = "No stocks yet"
            note_color = MUTED
        canvas.create_text(444, 244, anchor="nw", text=note, fill=note_color,
                           font=(FONT, 10, "bold"))

        # quick buttons
        row = tk.Frame(canvas, bg=SKY)
        make_button(row, "Deposit", self.show_deposit).pack(side="left", padx=(0, 10))
        make_button(row, "Withdraw", self.show_withdraw,
                    "secondary").pack(side="left", padx=(0, 10))
        make_button(row, "Transfer", self.show_transfer,
                    "secondary").pack(side="left", padx=(0, 10))
        make_button(row, "Open stock market", self.show_stocks,
                    "secondary").pack(side="left")
        canvas.create_window(60, 305, anchor="nw", window=row)

    # ----- deposit -----
    def show_deposit(self):
        self.set_active("Deposit")
        self.clear_content()
        self.heading("Deposit money", "Add cash to your account")
        form = self.form_card()
        self.amount_entry = self.field(form, "Amount (Rs.)")
        make_button(form, "Deposit", self.do_deposit).pack(fill="x", pady=(22, 0))

    def do_deposit(self):
        amount = self.read_amount()
        if amount is None:
            return
        ok, msg = db.deposit(self.current_acc, amount)
        if ok:
            messagebox.showinfo("Success", msg)
            self.show_home()
        else:
            messagebox.showerror("Error", msg)

    # ----- withdraw -----
    def show_withdraw(self):
        self.set_active("Withdraw")
        self.clear_content()
        self.heading("Withdraw money", "Take cash out of your account")
        form = self.form_card()
        self.amount_entry = self.field(form, "Amount (Rs.)")
        make_button(form, "Withdraw", self.do_withdraw).pack(fill="x", pady=(22, 0))

    def do_withdraw(self):
        amount = self.read_amount()
        if amount is None:
            return
        ok, msg = db.withdraw(self.current_acc, amount)
        if ok:
            messagebox.showinfo("Success", msg)
            self.show_home()
        else:
            messagebox.showerror("Error", msg)

    # ----- transfer -----
    def show_transfer(self):
        self.set_active("Transfer")
        self.clear_content()
        self.heading("Transfer money", "Send money to another account")
        form = self.form_card()
        self.to_entry = self.field(form, "Receiver account number")
        self.amount_entry = self.field(form, "Amount (Rs.)")
        make_button(form, "Send money", self.do_transfer).pack(fill="x", pady=(22, 0))

    def do_transfer(self):
        to_text = self.to_entry.get().strip()
        if not to_text.isdigit():
            messagebox.showerror("Error", "Please enter a valid account number")
            return
        amount = self.read_amount()
        if amount is None:
            return
        to_acc = int(to_text)
        receiver = db.get_account(to_acc)
        if receiver is None:
            messagebox.showerror("Error", "Receiver account not found")
            return
        sure = messagebox.askyesno(
            "Confirm transfer",
            f"Send Rs. {amount:.2f} to {receiver['name']} ({db.format_acc(to_acc)})?")
        if not sure:
            return
        ok, msg = db.transfer(self.current_acc, to_acc, amount)
        if ok:
            messagebox.showinfo("Success", msg)
            self.show_home()
        else:
            messagebox.showerror("Error", msg)

    # ----- stocks -----
    def show_stocks(self):
        self.set_active("Stocks")
        self.clear_content()
        self.stock_page = stock_page.StockPage(self)

        # ----- assistant -----
    def show_assistant(self):
        self.set_active("Assistant")
        self.clear_content()
        assistant_page.AssistantPage(self)
        
        # ----- statement -----
    def show_statement(self):
        self.set_active("Statement")
        self.clear_content()
        self.heading("Account statement", "All your transactions, newest first")
        self.make_table(db.get_statement(self.current_acc), height=14)

    # ---------------- admin ----------------
    def show_admin_login(self):
        form = self.auth_layout("Admin login", "Staff members only")
        self.admin_user = self.field(form, "Username")
        self.admin_pass = self.field(form, "Password", show="•")
        make_button(form, "Login", self.do_admin_login).pack(fill="x", pady=(26, 8))
        make_button(form, "Back", self.show_login, "secondary").pack(fill="x")

    def do_admin_login(self):
        user = self.admin_user.get().strip()
        password = self.admin_pass.get().strip()
        if db.admin_login(user, password):
            self.show_admin_panel()
        else:
            messagebox.showerror("Error", "Wrong username or password")

    def show_admin_panel(self):
        self.clear()
        page = tk.Frame(self.container, bg=BG, padx=55, pady=40)
        page.pack(fill="both", expand=True)

        top = tk.Frame(page, bg=BG)
        top.pack(fill="x")
        tk.Label(top, text="Admin panel", bg=BG, fg=TEXT,
                 font=(FONT, 26, "bold")).pack(side="left")
        make_button(top, "Logout", self.show_login, "secondary").pack(side="right")

        accounts = db.get_all_accounts()
        total_money = sum(a["balance"] for a in accounts)
        locked = sum(1 for a in accounts if a["locked"])

        stats = tk.Frame(page, bg=BG)
        stats.pack(fill="x", pady=22)
        numbers = [("Total accounts", len(accounts)),
                   ("Money in bank", f"Rs. {total_money:,.2f}"),
                   ("Locked accounts", locked)]
        for title, value in numbers:
            box = tk.Frame(stats, bg=SURFACE, padx=28, pady=16)
            box.pack(side="left", padx=(0, 18))
            tk.Label(box, text=title, bg=SURFACE, fg=MUTED,
                     font=(FONT, 10)).pack(anchor="w")
            tk.Label(box, text=str(value), bg=SURFACE, fg=TEXT,
                     font=(FONT, 20, "bold")).pack(anchor="w")

        # buttons are packed first so they stay visible at the bottom
        buttons = tk.Frame(page, bg=BG)
        buttons.pack(side="bottom", fill="x", pady=(18, 0))
        make_button(buttons, "Reset PIN", self.admin_reset_pin).pack(side="left")
        make_button(buttons, "Unlock account", self.admin_unlock,
                    "secondary").pack(side="left", padx=10)
        make_button(buttons, "Delete account", self.admin_delete,
                    "danger").pack(side="left")

        columns = ("Account", "Name", "Phone", "Balance", "Status")
        self.admin_table = ttk.Treeview(page, columns=columns, show="headings")
        for col in columns:
            self.admin_table.heading(col, text=col)
            self.admin_table.column(col, width=140, anchor="center")
        self.admin_table.tag_configure("odd", background="#f9fafb")
        for i, a in enumerate(accounts):
            status = "Locked" if a["locked"] else "Active"
            self.admin_table.insert("", "end", tags=("odd" if i % 2 else "even",),
                                    values=(db.format_acc(a["acc_no"]), a["name"],
                                            a["phone"], f"{a['balance']:.2f}", status))
        self.admin_table.pack(fill="both", expand=True)

    def selected_account(self):
        picked = self.admin_table.selection()
        if not picked:
            messagebox.showerror("Error", "Click an account in the table first")
            return None
        return int(self.admin_table.item(picked[0])["values"][0])

    def admin_reset_pin(self):
        acc_no = self.selected_account()
        if acc_no is None:
            return
        new_pin = simpledialog.askstring(
            "Reset PIN",
            f"Enter a new 4 digit PIN for account {db.format_acc(acc_no)}:",
            show="•", parent=self)
        if new_pin is None:
            return
        ok, msg = db.reset_pin(acc_no, new_pin.strip())
        if ok:
            messagebox.showinfo("Done", msg)
            self.show_admin_panel()
        else:
            messagebox.showerror("Error", msg)

    def admin_unlock(self):
        acc_no = self.selected_account()
        if acc_no is None:
            return
        db.unlock_account(acc_no)
        messagebox.showinfo("Done", f"Account {db.format_acc(acc_no)} unlocked")
        self.show_admin_panel()

    def admin_delete(self):
        acc_no = self.selected_account()
        if acc_no is None:
            return
        sure = messagebox.askyesno(
            "Delete account",
            f"Delete account {db.format_acc(acc_no)} for good?")
        if sure:
            db.delete_holdings(acc_no)
            db.delete_account(acc_no)
            self.show_admin_panel()


if __name__ == "__main__":
    db.setup_database()
    db.setup_stock_tables()
    BankApp().mainloop()