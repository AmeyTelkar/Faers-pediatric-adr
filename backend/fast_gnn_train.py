import os
import sqlalchemy as sa
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from app.routers.gnn import train_model_logic

print("Training GNN for 2024Q1...", flush=True)

res = train_model_logic(quarter="2024Q1")
print("GNN Training finished!", res, flush=True)
