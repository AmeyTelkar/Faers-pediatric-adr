from sqlalchemy import create_engine, text
from app.config import settings

engine = create_engine(settings.DATABASE_URL_SYNC)
query = """
INSERT INTO loaded_quarters (quarter, year, quarter_num, quarter_label, pediatric_rows, drug_rows, reaction_rows, signal_count, gnn_trained, superseded_rows)
VALUES ('2024Q1', 2024, 1, 'Q1 2024 (Jan-Mar)', 170411, 648146, 552337, 0, FALSE, 4052)
ON CONFLICT (quarter) DO NOTHING;
"""

def seed():
    with engine.begin() as conn:
        conn.execute(text(query))
        print("Seeded 2024Q1.")

if __name__ == '__main__':
    seed()
