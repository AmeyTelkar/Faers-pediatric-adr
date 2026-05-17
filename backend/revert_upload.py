from sqlalchemy import create_engine, text
from app.config import settings

BAD_SESSION = '246006f0-c74c-4d92-8900-9ddd886db984'
GOOD_SESSION = 'eeb647b9-7ee2-4a19-900e-2bc9fd612fdf'

engine = create_engine(settings.DATABASE_URL_SYNC)

def revert():
    with engine.begin() as conn:
        print("Rolling back tables based on primaryid mappings from demographics...")
        
        # We delete child tables by tracing back to the demographics primaryid for that bad session
        child_tables = ["drugs", "reactions", "outcomes", "report_sources", "therapy", "indications"]
        for table in child_tables:
            res = conn.execute(text(f"""
                DELETE FROM {table} 
                WHERE primaryid IN (
                    SELECT primaryid FROM demographics WHERE session_id = :sid
                )
            """), {"sid": BAD_SESSION})
            print(f"  {table}: {res.rowcount} rows deleted.")

        # Delete from demographics itself
        res = conn.execute(text("DELETE FROM demographics WHERE session_id = :sid"), {"sid": BAD_SESSION})
        print(f"  demographics: {res.rowcount} rows deleted.")

        # Re-calculate correct stats for the original 2025Q1
        demo = conn.execute(text("SELECT COUNT(*) FROM demographics WHERE source_quarter='2025Q1'")).scalar()
        drugs = conn.execute(text("SELECT COUNT(*) FROM drugs WHERE source_quarter='2025Q1'")).scalar()
        reactions = conn.execute(text("SELECT COUNT(*) FROM reactions WHERE source_quarter='2025Q1'")).scalar()
        
        # Restore the loaded_quarters entry for 2025Q1
        conn.execute(text("""
            UPDATE loaded_quarters 
            SET pediatric_rows = :ped, drug_rows = :drg, reaction_rows = :rac, session_id = :sid,
                superseded_rows = 4052
            WHERE quarter = '2025Q1'
        """), {
            "ped": demo, "drg": drugs, "rac": reactions, "sid": GOOD_SESSION
        })
        
        # Delete the bad session entirely from the history
        conn.execute(text("DELETE FROM upload_sessions WHERE session_id = :sid"), {"sid": BAD_SESSION})
        
        print(f"Restored 2025Q1. Original Demo Rows: {demo}")

if __name__ == "__main__":
    revert()
