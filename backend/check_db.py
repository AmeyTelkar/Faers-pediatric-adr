from app.database import get_sync_session
from sqlalchemy import text

session = get_sync_session()
sessions = session.execute(text("SELECT session_id, quarter, created_at FROM upload_sessions ORDER BY created_at DESC")).fetchall()
for s in sessions:
    count = session.execute(text(f"SELECT COUNT(*) FROM demographics WHERE session_id = '{s[0]}'")).scalar()
    print(f"Session {s[0]} ({s[1]}) on {s[2]}: {count} patients")
