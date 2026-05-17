"""
P1 Fix: Baseline comparisons (Logistic Regression & Random Forest)
Trains classical ML on flattened graph node features for comparison to GNN.
"""
import sys
sys.stdout.reconfigure(encoding='utf-8')

import torch
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import roc_auc_score
from torch_geometric.transforms import RandomLinkSplit

from app.database import get_sync_db
from app.gnn.graph_builder import build_gnn_graph

db = next(get_sync_db())

# Run on the most recent complete quarter
target_quarter = "2025Q4"
age_groups = ["ADOLESCENT", "CHILD", "INFANT", "NEONATE"]

print("=" * 70)
print(f"  PART 4: SAME-DATASET BASELINE COMPARISONS ({target_quarter})")
print("=" * 70)

results = {}

for age_group in age_groups:
    print(f"\nProcessing {age_group} @ {target_quarter}...")
    
    data, drug_idx, adr_idx, cohort_idx = build_gnn_graph(
        db, 
        age_group=age_group, 
        quarter=target_quarter
    )
    
    edge_type = ("drug", "reported_with", "adr")
    
    if edge_type not in data.edge_types or data[edge_type].edge_index.size(1) < 10:
        print(f"  Insufficient edges for {age_group}.")
        continue
        
    transform = RandomLinkSplit(
        num_val=0.1,
        num_test=0.1,
        is_undirected=False,
        edge_types=[edge_type],
        add_negative_train_samples=True,
    )
    
    train_data, val_data, test_data = transform(data)
    
    x_drug = data["drug"].x.numpy()
    x_adr = data["adr"].x.numpy()
    
    def extract_features(split_data):
        edge_index = split_data[edge_type].edge_label_index.numpy()
        labels = split_data[edge_type].edge_label.numpy()
        
        features = []
        for i in range(edge_index.shape[1]):
            u = edge_index[0, i]
            v = edge_index[1, i]
            features.append(np.concatenate([x_drug[u], x_adr[v]]))
            
        return np.array(features), labels

    X_train, y_train = extract_features(train_data)
    X_test, y_test = extract_features(test_data)
    
    print(f"  Train samples: {X_train.shape[0]}, Test samples: {X_test.shape[0]}")
    
    # Logistic Regression
    lr = LogisticRegression(max_iter=1000)
    lr.fit(X_train, y_train)
    lr_pred = lr.predict_proba(X_test)[:, 1]
    lr_auc = roc_auc_score(y_test, lr_pred)
    
    # Random Forest
    rf = RandomForestClassifier(n_estimators=100, max_depth=10, n_jobs=-1)
    rf.fit(X_train, y_train)
    rf_pred = rf.predict_proba(X_test)[:, 1]
    rf_auc = roc_auc_score(y_test, rf_pred)
    
    results[age_group] = {
        "LogReg": lr_auc,
        "RandomForest": rf_auc
    }
    
    print(f"  LogReg AUC: {lr_auc:.4f}")
    print(f"  RF AUC    : {rf_auc:.4f}")

print("\n\n" + "=" * 70)
print(f"  BASELINE COMPARISON SUMMARY ({target_quarter})")
print("=" * 70)
print(f"  {'Age Group':<15} | {'LogReg AUC':>12} | {'RF AUC':>12}")
print(f"  {'-'*45}")
for age_group in age_groups:
    if age_group in results:
        res = results[age_group]
        print(f"  {age_group:<15} | {res['LogReg']:12.4f} | {res['RandomForest']:12.4f}")
    else:
        print(f"  {age_group:<15} | {'N/A':>12} | {'N/A':>12}")
print("=" * 70)
