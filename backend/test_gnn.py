import pandas as pd
from app.database import get_sync_session
from sqlalchemy import text
from app.gnn.graph_builder import build_heterogeneous_graph

session = get_sync_session()
quarter = '2025Q3'
actual_age_group = 'CHILD'

demo_result = session.execute(text(
    f"SELECT primaryid, age_group FROM demographics "
    f"WHERE age_group IS NOT NULL AND is_superseded = FALSE AND source_quarter = '{quarter}'"
))
demo_df = pd.DataFrame(demo_result.fetchall(), columns=["primaryid", "age_group"])

drug_result = session.execute(text(
    f"SELECT primaryid, drugname_normalized, role_cod FROM drugs "
    f"WHERE is_superseded = FALSE AND source_quarter = '{quarter}'"
))
drug_df = pd.DataFrame(drug_result.fetchall(), columns=["primaryid", "drugname_normalized", "role_cod"])

reac_result = session.execute(text(
    f"SELECT primaryid, pt_term FROM reactions WHERE is_superseded = FALSE AND source_quarter = '{quarter}'"
))
reac_df = pd.DataFrame(reac_result.fetchall(), columns=["primaryid", "pt_term"])

print("Demo:", len(demo_df))
print("Drug:", len(drug_df))
print("Reac:", len(reac_df))

result = build_heterogeneous_graph(
    demo_df, drug_df, reac_df, actual_age_group,
)
print("Result[0] is None?", result[0] is None)

if result[0] is None:
    pids = set(demo_df[demo_df["age_group"] == actual_age_group]["primaryid"].astype(str))
    print("PIDs length:", len(pids))
    ps_drugs = drug_df[
        (drug_df["role_cod"] == "PS")
        & (drug_df["primaryid"].astype(str).isin(pids))
    ]
    reac = reac_df[reac_df["primaryid"].astype(str).isin(pids)]
    print("PS Drugs matches:", len(ps_drugs))
    print("Reactions matches:", len(reac))
    
    drug_names = ps_drugs["drugname_normalized"].dropna().unique().tolist()
    adr_terms = reac["pt_term"].dropna().unique().tolist()
    print("Unique adrs:", len(adr_terms))

from app.gnn.trainer import train_gnn_for_age_group
print("Running trainer instead!")
res = train_gnn_for_age_group(demo_df, drug_df, reac_df, model_key=actual_age_group + "_" + quarter, epochs=5)
print(res)
