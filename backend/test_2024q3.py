from app.database import sync_session_factory
from sqlalchemy import text

db = sync_session_factory()
res = db.execute(text("SELECT compute_faers_report('2024Q3', NULL)")).scalar()
print("Summary Signals:", res['summary']['total_signals'])
print("Table Signals:", len(res['top_signals']))
