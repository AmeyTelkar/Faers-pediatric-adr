import os
import fitz  # PyMuPDF
import re

pdf_dir = r"E:\Adverse drugs Project 2\8 resaerch paper"
out_file = "parsed_results.txt"

with open(out_file, "w", encoding="utf-8") as f:
    f.write("Analyzing Research Papers for FAERS Cleaning Methodologies...\n\n")

    for filename in os.listdir(pdf_dir):
        if not filename.endswith(".pdf"):
            continue
            
        filepath = os.path.join(pdf_dir, filename)
        f.write(f"--- Analyzing: {filename} ---\n")
        
        try:
            doc = fitz.open(filepath)
            found_snippets = []
            for page_num in range(doc.page_count):
                page = doc.load_page(page_num)
                text = page.get_text("text").replace("\n", " ")
                
                # Look for sections related to data extraction/preprocessing
                if re.search(r'(data\s*(?:source|collection|preprocessing|processing|cleaning|extraction|curation))', text, re.IGNORECASE):
                    # Extract surrounding context of keywords
                    sentences = text.split(". ")
                    for i, sentence in enumerate(sentences):
                        lower_sent = sentence.lower()
                        if "faers" in lower_sent or "fda" in lower_sent or "data" in lower_sent:
                            if any(kw in lower_sent for kw in ["deduplic", "remove", "exclude", "cleaning", "preprocessing", "caseid", "imput", "standardiz", "rxnorm", "filter"]):
                                # grab context
                                context = ". ".join(sentences[max(0, i-1):min(len(sentences), i+2)])
                                if context not in found_snippets:
                                    found_snippets.append(context)
                                    
            if found_snippets:
                f.write("Found Cleaning Methodology Snippets:\n")
                for s in found_snippets[:5]: # print top 5 matches per paper
                    f.write(f"  > {s[:500]}...\n")
            else:
                f.write("No direct cleaning methodology found.\n")
                
        except Exception as e:
            f.write(f"Error reading PDF: {e}\n")
        f.write("\n")
