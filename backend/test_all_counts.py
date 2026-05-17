from app.database import sync_session_factory
from sqlalchemy import text
import time

db = sync_session_factory()

# Get all quarters
quarters = db.execute(text("SELECT DISTINCT source_quarter FROM demographics WHERE is_superseded = FALSE ORDER BY source_quarter")).fetchall()
quarters = [q[0] for q in quarters]

mismatches = 0
print("Testing all quarters for count mismatches...\n")
print(f"{'Quarter':<10} | {'Demographics Tab':<20} | {'Report Builder':<20} | {'Status'}")
print("-" * 70)

# Test ALL first
demo_count_all = db.execute(text("SELECT COUNT(*) FROM demographics WHERE is_superseded = FALSE")).scalar()
report_count_all = dict(db.execute(text("SELECT compute_faers_report(NULL, NULL)")).scalar())['summary']['total_patients']

status = "PASS" if demo_count_all == report_count_all else "FAIL"
if status == "FAIL": mismatches += 1
print(f"{'ALL':<10} | {demo_count_all:<20} | {report_count_all:<20} | {status}")

# Test each quarter
for q in quarters:
    demo_count = db.execute(text(f"SELECT COUNT(*) FROM demographics WHERE is_superseded = FALSE AND source_quarter = '{q}'")).scalar()
    report_count = dict(db.execute(text(f"SELECT compute_faers_report('{q}', NULL)")).scalar())['summary']['total_patients']
    
    status = "PASS" if demo_count == report_count else "FAIL"
    if status == "FAIL": mismatches += 1
    print(f"{q:<10} | {demo_count:<20} | {report_count:<20} | {status}")

print(f"\nTotal Mismatches Found: {mismatches}")
