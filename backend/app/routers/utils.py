"""
Shared utilities for routers.
"""

def build_quarter_filter(quarter: str, prefix: str = "") -> tuple[str, dict]:
    """
    Builds the WHERE clause for quarter filtering.
    quarter = 'ALL'        -> no filter (all data)
    quarter = '2024Q1'     -> specific quarter
    quarter = '2024_ALL'   -> all quarters in 2024
    
    prefix: Optional table alias e.g., 'd.' or 'r.'
    """
    if quarter == 'ALL' or not quarter:
        return "", {}
        
    col = f"{prefix}source_quarter" if prefix else "source_quarter"
        
    if quarter.endswith('_ALL'):
        year = int(quarter.split('_')[0])
        return f"AND {col} IN (SELECT quarter FROM loaded_quarters WHERE year = :yr)", {"yr": year}
        
    return f"AND {col} = :quarter", {"quarter": quarter}
