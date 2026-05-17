from app.database import sync_session_factory
from sqlalchemy import text
db = sync_session_factory()
res = db.execute(text("SELECT compute_faers_report('2021Q1', NULL)")).scalar()
print(dict(res)['summary']['total_patients'])
