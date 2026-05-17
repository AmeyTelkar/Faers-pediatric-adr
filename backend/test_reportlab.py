import time
from reportlab.platypus import SimpleDocTemplate, Table
from reportlab.lib.pagesizes import letter

print("Building PDF with 6500 rows...")
start = time.time()
doc = SimpleDocTemplate("test_6500.pdf", pagesize=letter)
rows = [["Col1", "Col2", "Col3", "Col4", "Col5"]]
for i in range(6500):
    rows.append([str(i), "DrugNameTest", "ADRNameTest", "CHILD", "100"])

tbl = Table(rows)
doc.build([tbl])
print(f"Done in {time.time()-start:.2f}s")
