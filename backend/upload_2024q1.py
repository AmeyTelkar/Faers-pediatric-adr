import os
import time
import requests

API_URL = "http://localhost:8000/api/upload"
DATA_DIR = r"E:\Adverse drugs Project 2\faers-pediatric-adr\data\2024\faers_ascii_2024q1\ascii"
QUARTER = "2024Q1"
YEAR = 2024

files_to_upload = [
    "DEMO24Q1.txt", "DRUG24Q1.txt", "INDI24Q1.txt",
    "OUTC24Q1.txt", "REAC24Q1.txt", "RPSR24Q1.txt", "THER24Q1.txt"
]

print(f"Uploading {QUARTER} data...")

# Prepare files for multipart upload
files_payload = []
file_handles = []
for fname in files_to_upload:
    fpath = os.path.join(DATA_DIR, fname)
    if os.path.exists(fpath):
        f = open(fpath, "rb")
        file_handles.append(f)
        files_payload.append(("files", (fname, f, "text/plain")))
    else:
        print(f"Warning: {fpath} not found")

try:
    data_payload = {"quarter": QUARTER, "year": YEAR}
    res = requests.post(f"{API_URL}/ingest", files=files_payload, data=data_payload)
    res.raise_for_status()
    task_id = res.json()["task_id"]
    print(f"Ingest started with task_id: {task_id}")

    # Poll status
    while True:
        status_res = requests.get(f"{API_URL}/task/{task_id}").json()
        status = status_res["status"]
        if status == "ready":
            print("Processing complete! Approving...")
            break
        elif status == "failed":
            print("Failed:", status_res.get("error"))
            exit(1)
        
        print(f"Status: {status}... waiting 3s")
        time.sleep(3)

    # Approve
    approve_res = requests.post(f"{API_URL}/approve/{task_id}")
    approve_res.raise_for_status()
    print("Database insert successful!")
    print(approve_res.json())

finally:
    for f in file_handles:
        f.close()
