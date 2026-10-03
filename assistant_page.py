import tkinter as tk
from tkinter import ttk
import database as db
from chatbot import Chatbot
from ui import (BG, SURFACE, TINT, BORDER, TEXT, MUTED, ACCENT, FONT,
                make_button, make_entry, with_loading)

# every account keeps its own chat while the program is open
CHATS = {}

# quick question buttons shown under the chat
CHIPS = [
    ["How do I deposit money?", "How do I transfer money?", "How do I buy stocks?"],
    ["Which stock should I buy?", "Show me safe stocks", "How is the market today?"],
]


class AssistantPage:
    # the chat screen for AR Assistant

    def __init__(self, app):
        self.app = app
        acc_no = app.current_acc
        if acc_no not in CHATS:
            CHATS[acc_no] = {"bot": Chatbot(app.market), "log": []}
        self.chat = CHATS[acc_no]
        self.build()

        if self.chat["log"]:
            for who, text in self.chat["log"]:  # show the earlier messages again
                self.draw_message(who, text)
        else:
            name = db.get_account(acc_no)["name"]
            self.add_message("bot", self.welcome(name))

    def welcome(self, name):
        return (f"Hi {name}! I'm AR Assistant. I can:\n"
                "- explain how to use AR Bank (deposit, withdraw, transfer, statement, PIN problems)\n"
                "- show your balance and your stock portfolio\n"
                "- look at the live practice market and suggest which stocks to look at\n"
                "- explain words like dividend, risk and diversification\n\n"
                "I work completely offline. Tap one of the buttons below or type your own question.")

    # ---------------- building the screen ----------------
    def build(self):
        root = tk.Frame(self.app.content, bg=BG)
        root.pack(fill="both", expand=True)
        tk.Label(root, text="AR Assistant", bg=BG, fg=TEXT,
                 font=(FONT, 26, "bold")).pack(anchor="w")
        tk.Label(root, text="Ask how to use AR Bank or which practice stock to look at. "
                            "Works fully offline.",
                 bg=BG, fg=MUTED, font=(FONT, 12)).pack(anchor="w", pady=(2, 16))

        # the bottom part is packed first so it always stays visible
        bottom = tk.Frame(root, bg=BG)
        bottom.pack(side="bottom", fill="x", pady=(14, 0))
        for texts in CHIPS:
            row = tk.Frame(bottom, bg=BG)
            row.pack(anchor="w", pady=(0, 6))
            for text in texts:
                self.chip(row, text)
        entry_row = tk.Frame(bottom, bg=BG)
        entry_row.pack(fill="x", pady=(8, 0))
        make_button(entry_row, "Send", self.send).pack(side="right", padx=(12, 0))
        self.entry = make_entry(entry_row)
        self.entry.pack(side="left", fill="x", expand=True, ipady=10)
        self.entry.bind("<Return>", lambda e: with_loading(self.send)())
        self.entry.focus_set()

        # the chat messages
        frame = tk.Frame(root, bg=BG, highlightthickness=1, highlightbackground=BORDER)
        frame.pack(fill="both", expand=True)
        scroll = ttk.Scrollbar(frame)
        scroll.pack(side="right", fill="y")
        self.box = tk.Text(frame, wrap="word", bg=BG, fg=TEXT, bd=0,
                           highlightthickness=0, font=(FONT, 12), padx=22, pady=12,
                           cursor="arrow", state="disabled", yscrollcommand=scroll.set)
        self.box.pack(side="left", fill="both", expand=True)
        scroll.config(command=self.box.yview)

        self.box.tag_configure("bot_name", font=(FONT, 9, "bold"), foreground=ACCENT,
                               spacing1=16, lmargin1=8)
        self.box.tag_configure("bot", background=SURFACE, foreground=TEXT, lmargin1=16,
                               lmargin2=16, rmargin=160, spacing1=6, spacing3=6)
        self.box.tag_configure("user_name", font=(FONT, 9, "bold"), foreground=MUTED,
                               justify="right", spacing1=16, rmargin=8)
        self.box.tag_configure("user", background=TINT, foreground=TEXT, justify="right",
                               lmargin1=160, lmargin2=160, rmargin=16, spacing1=6,
                               spacing3=6)

    def chip(self, parent, text):
        # a small button that asks a ready-made question
        btn = tk.Button(parent, text=text, command=with_loading(lambda: self.send(text)),
                        bg="#eef0f3", fg=TEXT, font=(FONT, 10), relief="flat", bd=0,
                        padx=14, pady=7, cursor="hand2", activebackground="#e2e5ea")
        btn.pack(side="left", padx=(0, 8))
        btn.bind("<Enter>", lambda e: btn.config(bg="#e2e5ea"))
        btn.bind("<Leave>", lambda e: btn.config(bg="#eef0f3"))

    # ---------------- messages ----------------
    def draw_message(self, who, text):
        self.box.config(state="normal")
        if who == "bot":
            self.box.insert("end", "AR Assistant\n", "bot_name")
            self.box.insert("end", text + "\n", "bot")
        else:
            self.box.insert("end", "You\n", "user_name")
            self.box.insert("end", text + "\n", "user")
        self.box.config(state="disabled")
        self.box.see("end")

    def add_message(self, who, text):
        self.chat["log"].append((who, text))
        self.draw_message(who, text)

    def send(self, text=None):
        if text is None:  # typed by the user
            text = self.entry.get().strip()
            self.entry.delete(0, "end")
        if text == "":
            return
        self.add_message("user", text)
        answer = self.chat["bot"].reply(text, self.app.current_acc)
        self.add_message("bot", answer)