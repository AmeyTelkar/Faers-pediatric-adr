from app.database import get_sync_session
from sqlalchemy import text

session = get_sync_session()

demo_count = session.execute(text("SELECT COUNT(*) FROM demographics WHERE age_group = 'CHILD' AND source_quarter = '2025Q3' AND is_superseded = FALSE")).scalar()
drug_count = session.execute(text("SELECT COUNT(*) FROM drugs WHERE source_quarter = '2025Q3' AND is_superseded = FALSE")).scalar()
reac_count = session.execute(text("SELECT COUNT(*) FROM reactions WHERE source_quarter = '2025Q3' AND is_superseded = FALSE")).scalar()

print(f"CHILD DEMO Q3: {demo_count}")
print(f"DRUGS Q3: {drug_count}")
print(f"REACTIONS Q3: {reac_count}")
