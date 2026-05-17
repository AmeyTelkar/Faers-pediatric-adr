from sqlalchemy import create_engine, text
from app.config import settings

engine = create_engine(settings.DATABASE_URL_SYNC)

def fix():
    with engine.begin() as conn:
        conn.execute(text("UPDATE loaded_quarters SET superseded_rows = 0 WHERE quarter = '2025Q1'"))
        print("Set 2025Q1 dedup back to 0")

if __name__ == '__main__':
    fix()
