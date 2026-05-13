import os
import csv
import sys

# Add repo root to path so pipeline imports work
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from pipeline.extractor import extract_text
from pipeline.chunker import chunk_text
from io import BytesIO

# --- Configure these paths to match your data folder structure ---
FILES = [
    # Interviews
    ("data/synthetic/revolut/interview_revolut_01.txt", "interview"),
    ("data/synthetic/asana/interview_asana_01.txt", "interview"),
    ("data/synthetic/lidl_plus_app/interview_lidl_01.txt", "interview"),

    # Tickets (CSV)
    ("data/synthetic/revolut/tickets_revolut.csv", "ticket"),
    ("data/synthetic/asana/tickets_asana.csv", "ticket"),
    ("data/synthetic/lidl_plus_app/tickets_lidl.csv", "ticket"),

    # Reviews (CSV)
    ("data/synthetic/revolut/reviews_revolut.csv", "review"),
    ("data/synthetic/asana/reviews_asana.csv", "review"),
    ("data/synthetic/lidl_plus_app/lidl_plus_reviews.csv", "review"),
]

OUTPUT_CSV = "notebooks/chunks_for_labelling.csv"

rows = []
for filepath, source_type in FILES:
    filename = os.path.basename(filepath)
    with open(filepath, "rb") as f:
        file_bytes = BytesIO(f.read())
        file_bytes.name = filename  # extractor may need the filename
    raw_text = extract_text(file_bytes, source_type)
    chunks = chunk_text(raw_text, filename, source_type)
    for c in chunks:
        rows.append({
            "chunk_id": c["chunk_id"],
            "text": c["text"],
            "source_type": c["source_type"],
            "label": ""
        })

with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=["chunk_id", "text", "source_type", "label"])
    writer.writeheader()
    writer.writerows(rows)

print(f"Done. {len(rows)} chunks written to {OUTPUT_CSV}")