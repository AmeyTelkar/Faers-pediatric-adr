import os
import fitz  # PyMuPDF
import re

pdf_dir = r"E:\Adverse drugs Project 2\8 resaerch paper"

keywords = ["clean", "preprocess", "deduplic", "caseid", "caseversion", "val_vbm", "primaryid", "adult", "pediatric filter", "18", "years", "2021", "2022", "2023", "2024", "2025"]

print("Analyzing Research Papers for FAERS Cleaning Methodologies...\n")

for filename in os.listdir(pdf_dir):
    if not filename.endswith(".pdf"):
        continue
        
    filepath = os.path.join(pdf_dir, filename)
    print(f"--- Analyzing: {filename} ---")
    
    try:
        doc = fitz.open(filepath)
        found_snippets = []
        for page_num in range(doc.page_count):
            page = doc.load_page(page_num)
            text = page.get_text("text").replace("\n", " ")
            
            # Look for sections related to data extraction/preprocessing
            if re.search(r'(data\s*(?:source|collection|preprocessing|processing|cleaning|extraction))', text, re.IGNORECASE):
                # Extract surrounding context of keywords
                sentences = text.split(". ")
                for i, sentence in enumerate(sentences):
                    lower_sent = sentence.lower()
                    if "faers" in lower_sent or "fda" in lower_sent or "data" in lower_sent:
                        if any(kw in lower_sent for kw in ["deduplic", "remove", "exclude", "cleaning", "preprocessing", "caseid"]):
                            # grab context
                            context = ". ".join(sentences[max(0, i-1):min(len(sentences), i+2)])
                            if context not in found_snippets:
                                found_snippets.append(context)
                                
        if found_snippets:
            print("Found Cleaning Methodology Snippets:")
            for s in found_snippets[:3]: # print top 3 matches per paper
                print(f"  > {s[:400]}...")
        else:
            print("No direct cleaning methodology found.")
            
    except Exception as e:
        print(f"Error reading PDF: {e}")
    print("\n")
