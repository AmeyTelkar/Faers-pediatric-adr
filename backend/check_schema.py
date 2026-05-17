from app.database import get_sync_db
from sqlalchemy import text
db = next(get_sync_db())

# Check loaded_quarters schema
print("=== loaded_quarters columns ===")
r = db.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name = 'loaded_quarters' ORDER BY ordinal_position"))
for row in r.fetchall():
    print(row[0])

# Check actual data
print("\n=== loaded_quarters data ===")
r = db.execute(text("SELECT * FROM loaded_quarters LIMIT 3"))
cols = r.keys()
print("Columns:", list(cols))
for row in r.fetchall():
    print(row)
