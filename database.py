import sqlite3
import hashlib
import os
from datetime import datetime

DB_NAME = "bank.db"


def connect():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn


def hash_pin(pin, salt):
    # we never store the real PIN, only this scrambled version
    return hashlib.sha256((salt + pin).encode()).hexdigest()


def setup_database():
    conn = connect()
    cur = conn.cursor()
    cur.execute("""CREATE TABLE IF NOT EXISTS accounts (
        acc_no INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        phone TEXT,
        pin_hash TEXT NOT NULL,
        salt TEXT NOT NULL,
        balance REAL DEFAULT 0,
        failed_attempts INTEGER DEFAULT 0,
        locked INTEGER DEFAULT 0,
        created_at TEXT)""")
    cur.execute("""CREATE TABLE IF NOT EXISTS transactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        acc_no INTEGER,
        type TEXT,
        amount REAL,
        balance_after REAL,
        note TEXT,
        created_at TEXT)""")
    cur.execute("""CREATE TABLE IF NOT EXISTS admin (
        username TEXT PRIMARY KEY,
        password_hash TEXT,
        salt TEXT)""")

    # make a default admin the first time only
    cur.execute("SELECT COUNT(*) FROM admin")
    if cur.fetchone()[0] == 0:
        salt = os.urandom(8).hex()
        cur.execute("INSERT INTO admin VALUES (?, ?, ?)",
                    ("admin", hash_pin("admin123", salt), salt))
    conn.commit()
    conn.close()


def now():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def format_acc(acc_no):
    return str(acc_no).zfill(5)  # 1 becomes 00001


def create_account(name, phone, pin):
    if not pin.isdigit() or len(pin) != 4:
        return None, "PIN must be exactly 4 digits"
    salt = os.urandom(8).hex()
    conn = connect()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO accounts (name, phone, pin_hash, salt, created_at) VALUES (?, ?, ?, ?, ?)",
        (name, phone, hash_pin(pin, salt), salt, now()))
    acc_no = cur.lastrowid
    conn.commit()
    conn.close()
    return acc_no, "Account created"


def login(acc_no, pin):
    conn = connect()
    cur = conn.cursor()
    cur.execute("SELECT * FROM accounts WHERE acc_no = ?", (acc_no,))
    acc = cur.fetchone()
    if acc is None:
        conn.close()
        return False, "Account not found"
    if acc["locked"]:
        conn.close()
        return False, "Account is locked. Contact admin."

    if hash_pin(pin, acc["salt"]) == acc["pin_hash"]:
        cur.execute("UPDATE accounts SET failed_attempts = 0 WHERE acc_no = ?", (acc_no,))
        conn.commit()
        conn.close()
        return True, "Login successful"

    attempts = acc["failed_attempts"] + 1
    locked = 1 if attempts >= 3 else 0
    cur.execute("UPDATE accounts SET failed_attempts = ?, locked = ? WHERE acc_no = ?",
                (attempts, locked, acc_no))
    conn.commit()
    conn.close()
    if locked:
        return False, "Too many wrong attempts. Account locked."
    return False, f"Wrong PIN. {3 - attempts} attempt(s) left."


def get_balance(acc_no):
    conn = connect()
    row = conn.execute("SELECT balance FROM accounts WHERE acc_no = ?", (acc_no,)).fetchone()
    conn.close()
    return row["balance"] if row else None


def _record(cur, acc_no, kind, amount, new_balance, note):
    cur.execute(
        "INSERT INTO transactions (acc_no, type, amount, balance_after, note, created_at) VALUES (?, ?, ?, ?, ?, ?)",
        (acc_no, kind, amount, new_balance, note, now()))


def deposit(acc_no, amount):
    if amount <= 0:
        return False, "Amount must be more than 0"
    conn = connect()
    cur = conn.cursor()
    bal = cur.execute("SELECT balance FROM accounts WHERE acc_no = ?", (acc_no,)).fetchone()["balance"]
    new_bal = round(bal + amount, 2)
    cur.execute("UPDATE accounts SET balance = ? WHERE acc_no = ?", (new_bal, acc_no))
    _record(cur, acc_no, "Deposit", amount, new_bal, "Cash deposit")
    conn.commit()
    conn.close()
    return True, "Deposit successful"


def withdraw(acc_no, amount):
    if amount <= 0:
        return False, "Amount must be more than 0"
    conn = connect()
    cur = conn.cursor()
    bal = cur.execute("SELECT balance FROM accounts WHERE acc_no = ?", (acc_no,)).fetchone()["balance"]
    if amount > bal:
        conn.close()
        return False, "Insufficient balance"
    new_bal = round(bal - amount, 2)
    cur.execute("UPDATE accounts SET balance = ? WHERE acc_no = ?", (new_bal, acc_no))
    _record(cur, acc_no, "Withdrawal", amount, new_bal, "Cash withdrawal")
    conn.commit()
    conn.close()
    return True, "Withdrawal successful"


def transfer(from_acc, to_acc, amount):
    if amount <= 0:
        return False, "Amount must be more than 0"
    if from_acc == to_acc:
        return False, "Cannot transfer to the same account"
    conn = connect()
    cur = conn.cursor()
    receiver = cur.execute("SELECT balance FROM accounts WHERE acc_no = ?", (to_acc,)).fetchone()
    if receiver is None:
        conn.close()
        return False, "Receiver account not found"
    sender_bal = cur.execute("SELECT balance FROM accounts WHERE acc_no = ?", (from_acc,)).fetchone()["balance"]
    if amount > sender_bal:
        conn.close()
        return False, "Insufficient balance"

    new_sender = round(sender_bal - amount, 2)
    new_receiver = round(receiver["balance"] + amount, 2)
    cur.execute("UPDATE accounts SET balance = ? WHERE acc_no = ?", (new_sender, from_acc))
    cur.execute("UPDATE accounts SET balance = ? WHERE acc_no = ?", (new_receiver, to_acc))
    _record(cur, from_acc, "Transfer Out", amount, new_sender, f"To {format_acc(to_acc)}")
    _record(cur, to_acc, "Transfer In", amount, new_receiver, f"From {format_acc(from_acc)}")
    conn.commit()  # both updates are saved together, or not at all
    conn.close()
    return True, "Transfer successful"


def get_statement(acc_no, limit=None):
    conn = connect()
    query = "SELECT * FROM transactions WHERE acc_no = ? ORDER BY id DESC"
    if limit:
        query += f" LIMIT {int(limit)}"
    rows = conn.execute(query, (acc_no,)).fetchall()
    conn.close()
    return rows


# ---------- admin functions ----------

def admin_login(username, password):
    conn = connect()
    row = conn.execute("SELECT * FROM admin WHERE username = ?", (username,)).fetchone()
    conn.close()
    return bool(row) and hash_pin(password, row["salt"]) == row["password_hash"]


def get_all_accounts():
    conn = connect()
    rows = conn.execute("SELECT * FROM accounts ORDER BY acc_no").fetchall()
    conn.close()
    return rows


def reset_pin(acc_no, new_pin):
    if not new_pin.isdigit() or len(new_pin) != 4:
        return False, "PIN must be exactly 4 digits"
    salt = os.urandom(8).hex()
    conn = connect()
    conn.execute("UPDATE accounts SET pin_hash = ?, salt = ?, failed_attempts = 0, locked = 0 WHERE acc_no = ?",
                 (hash_pin(new_pin, salt), salt, acc_no))
    conn.commit()
    conn.close()
    return True, "PIN reset and account unlocked"


def delete_account(acc_no):
    conn = connect()
    conn.execute("DELETE FROM accounts WHERE acc_no = ?", (acc_no,))
    conn.commit()
    conn.close()
    

def get_account(acc_no):
    conn = connect()
    row = conn.execute("SELECT * FROM accounts WHERE acc_no = ?", (acc_no,)).fetchone()
    conn.close()
    return row


def unlock_account(acc_no):
    conn = connect()
    conn.execute("UPDATE accounts SET locked = 0, failed_attempts = 0 WHERE acc_no = ?", (acc_no,))
    conn.commit()
    conn.close()
    

# ---------- stock market functions ----------

def setup_stock_tables():
    conn = connect()
    conn.execute("""CREATE TABLE IF NOT EXISTS holdings (
        acc_no INTEGER,
        symbol TEXT,
        qty INTEGER,
        avg_price REAL,
        PRIMARY KEY (acc_no, symbol))""")
    conn.commit()
    conn.close()


def get_holdings(acc_no):
    conn = connect()
    rows = conn.execute("SELECT * FROM holdings WHERE acc_no = ? ORDER BY symbol",
                        (acc_no,)).fetchall()
    conn.close()
    return rows


def buy_stock(acc_no, symbol, qty, price):
    if qty <= 0:
        return False, "Quantity must be at least 1"
    cost = round(qty * price, 2)
    conn = connect()
    cur = conn.cursor()
    bal = cur.execute("SELECT balance FROM accounts WHERE acc_no = ?", (acc_no,)).fetchone()["balance"]
    if cost > bal:
        conn.close()
        return False, "Insufficient balance in your account"

    new_bal = round(bal - cost, 2)
    cur.execute("UPDATE accounts SET balance = ? WHERE acc_no = ?", (new_bal, acc_no))

    row = cur.execute("SELECT qty, avg_price FROM holdings WHERE acc_no = ? AND symbol = ?",
                      (acc_no, symbol)).fetchone()
    if row is None:
        cur.execute("INSERT INTO holdings VALUES (?, ?, ?, ?)", (acc_no, symbol, qty, price))
    else:
        total_qty = row["qty"] + qty
        new_avg = round((row["qty"] * row["avg_price"] + qty * price) / total_qty, 2)
        cur.execute("UPDATE holdings SET qty = ?, avg_price = ? WHERE acc_no = ? AND symbol = ?",
                    (total_qty, new_avg, acc_no, symbol))

    _record(cur, acc_no, "Stock Buy", cost, new_bal, f"{qty} x {symbol} @ {price:.2f}")
    conn.commit()
    conn.close()
    return True, f"Bought {qty} share(s) of {symbol}"


def sell_stock(acc_no, symbol, qty, price):
    if qty <= 0:
        return False, "Quantity must be at least 1"
    conn = connect()
    cur = conn.cursor()
    row = cur.execute("SELECT qty FROM holdings WHERE acc_no = ? AND symbol = ?",
                      (acc_no, symbol)).fetchone()
    if row is None or row["qty"] < qty:
        conn.close()
        return False, "You do not own that many shares"

    money = round(qty * price, 2)
    bal = cur.execute("SELECT balance FROM accounts WHERE acc_no = ?", (acc_no,)).fetchone()["balance"]
    new_bal = round(bal + money, 2)
    cur.execute("UPDATE accounts SET balance = ? WHERE acc_no = ?", (new_bal, acc_no))

    left = row["qty"] - qty
    if left == 0:
        cur.execute("DELETE FROM holdings WHERE acc_no = ? AND symbol = ?", (acc_no, symbol))
    else:
        cur.execute("UPDATE holdings SET qty = ? WHERE acc_no = ? AND symbol = ?",
                    (left, acc_no, symbol))

    _record(cur, acc_no, "Stock Sell", money, new_bal, f"{qty} x {symbol} @ {price:.2f}")
    conn.commit()
    conn.close()
    return True, f"Sold {qty} share(s) of {symbol}"


def delete_holdings(acc_no):
    conn = connect()
    conn.execute("DELETE FROM holdings WHERE acc_no = ?", (acc_no,))
    conn.commit()
    conn.close()