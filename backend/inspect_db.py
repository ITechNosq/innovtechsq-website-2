import sqlite3
import os

db_path = r'e:\InnovTech Sq\new web site 23-4-2026\backend\leads.db'

if not os.path.exists(db_path):
    print(f"Database file not found at {db_path}")
    exit(1)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Get tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = cursor.fetchall()
print(f"Tables: {[t[0] for t in tables]}")

for table in [t[0] for t in tables]:
    print(f"\n--- Table: {table} ---")
    
    # Get schema
    cursor.execute(f"PRAGMA table_info({table});")
    columns = cursor.fetchall()
    print("Columns:")
    for col in columns:
        print(f"  {col[1]} ({col[2]}) {'NOT NULL' if col[3] else ''} {'PK' if col[5] else ''}")
    
    # Get record count
    cursor.execute(f"SELECT COUNT(*) FROM {table};")
    count = cursor.fetchone()[0]
    print(f"Record count: {count}")
    
    # Get last 5 records if any
    if count > 0:
        print("Last 5 records:")
        cursor.execute(f"SELECT * FROM {table} ORDER BY id DESC LIMIT 5;")
        rows = cursor.fetchall()
        for row in rows:
            print(f"  {row}")

conn.close()
