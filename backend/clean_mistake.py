import sys
from app.database import get_sync_session
from sqlalchemy import text

def clean_mistake():
    session_id = 'eeb647b9-7ee2-4a19-900e-2bc9fd612fdf'
    session = get_sync_session()
    
    print("Deleting child tables...")
    session.execute(text(f"""
        DELETE FROM drugs WHERE primaryid IN (SELECT primaryid FROM demographics WHERE session_id = '{session_id}')
    """))
    session.execute(text(f"""
        DELETE FROM reactions WHERE primaryid IN (SELECT primaryid FROM demographics WHERE session_id = '{session_id}')
    """))
    session.execute(text(f"""
        DELETE FROM outcomes WHERE primaryid IN (SELECT primaryid FROM demographics WHERE session_id = '{session_id}')
    """))
    session.execute(text(f"""
        DELETE FROM report_sources WHERE primaryid IN (SELECT primaryid FROM demographics WHERE session_id = '{session_id}')
    """))
    session.execute(text(f"""
        DELETE FROM therapy WHERE primaryid IN (SELECT primaryid FROM demographics WHERE session_id = '{session_id}')
    """))
    session.execute(text(f"""
        DELETE FROM indications WHERE primaryid IN (SELECT primaryid FROM demographics WHERE session_id = '{session_id}')
    """))
    
    print("Deleting demographics...")
    session.execute(text(f"DELETE FROM demographics WHERE session_id = '{session_id}'"))
    
    print("Fixing Q1 metadata label...")
    session.execute(text("UPDATE loaded_quarters SET pediatric_rows = 168994 WHERE quarter = '2025Q1'"))
    
    session.commit()
    print("Cleanup complete!")

if __name__ == "__main__":
    clean_mistake()
