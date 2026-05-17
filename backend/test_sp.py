import sys
from app.database import sync_session_factory
from sqlalchemy import text

db = sync_session_factory()
try:
    res = db.execute(
        text("SELECT compute_faers_report(:q, NULL)"),
        {"q": "2025Q4"}
    ).scalar()
    print("Success, keys:", res.keys() if res else "No result")
except Exception as e:
    print("Error:", e)
