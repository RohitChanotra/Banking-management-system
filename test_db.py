import database as db

db.setup_database()
acc, msg = db.create_account("Test User", "9999999999", "1234")
print(msg, "- account number:", db.format_acc(acc))
print(db.deposit(acc, 5000))
print(db.withdraw(acc, 1200))
print("Balance:", db.get_balance(acc))
print(db.login(acc, "0000"))
print(db.login(acc, "1234"))