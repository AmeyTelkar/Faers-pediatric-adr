import time
import os
import json

CACHE_DIR = "report_cache_data"
CACHE_TTL_SECONDS = 86400 * 7  # 7 days

if not os.path.exists(CACHE_DIR):
    os.makedirs(CACHE_DIR)

def cache_key(quarter: str | None, age_group: str | None) -> str:
    q = quarter or "ALL"
    a = (age_group or "all").replace(" ", "_").replace("<", "lt").replace(">", "gt")
    return f"faers_report_{q}_{a}.json"

def get_cached_report(quarter, age_group) -> dict | None:
    filename = cache_key(quarter, age_group)
    filepath = os.path.join(CACHE_DIR, filename)
    
    if os.path.exists(filepath):
        if (time.time() - os.path.getmtime(filepath)) < CACHE_TTL_SECONDS:
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception:
                pass
    return None

def set_cached_report(quarter, age_group, data: dict):
    filename = cache_key(quarter, age_group)
    filepath = os.path.join(CACHE_DIR, filename)
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f)
    except Exception as e:
        print(f"Failed to write cache to disk: {e}")

def invalidate_all_report_cache():
    """Call this after new data upload."""
    for filename in os.listdir(CACHE_DIR):
        if filename.endswith(".json"):
            try:
                os.remove(os.path.join(CACHE_DIR, filename))
            except:
                pass
