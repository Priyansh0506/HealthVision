import sqlite3

conn = sqlite3.connect("disease.db")
cur = conn.cursor()

cur.execute("SELECT * FROM users")
rows = cur.fetchall()

print(rows)

conn.close()