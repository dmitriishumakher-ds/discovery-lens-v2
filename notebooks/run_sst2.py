import os, sys, time, tracemalloc, numpy as np, pandas as pd

os.chdir(os.path.expanduser("~/capstone/discovery-lens"))
sys.path.insert(0, ".")

df = pd.read_csv("notebooks/chunks_for_labelling_sample.csv")
df["label"] = df["label"].astype(str).replace("nan", "")
texts = df["text"].tolist()
true_labels = df["label"].tolist()
print(df["label"].value_counts())

from transformers import pipeline

print("Loading distilbert-sst2...")
sst2 = pipeline("sentiment-analysis", model="distilbert-base-uncased-finetuned-sst-2-english", framework="tf")

def sst2_label(result):
    return "positive" if result["label"] == "POSITIVE" else "negative"

def run_in_batches(pipe, texts, batch_size=8):
    results = []
    for i in range(0, len(texts), batch_size):
        results.extend(pipe(texts[i:i+batch_size], truncation=True, max_length=512))
    return results

tracemalloc.start()
start = time.time()
sst2_results = run_in_batches(sst2, texts)
elapsed = time.time() - start
_, peak = tracemalloc.get_traced_memory()
tracemalloc.stop()

sst2_labels = [sst2_label(r) for r in sst2_results]
sst2_scores = [r["score"] if r["label"] == "POSITIVE" else -r["score"] for r in sst2_results]
acc = sum(p == t for p, t in zip(sst2_labels, true_labels)) / len(true_labels)
spread = np.std(sst2_scores)

print(f"DistilBERT-SST2 accuracy:  {acc:.2%}")
print(f"DistilBERT-SST2 spread:    {spread:.4f}")
print(f"DistilBERT-SST2 time:      {elapsed:.3f}s")
print(f"DistilBERT-SST2 peak RAM:  {peak / 1024**2:.1f} MB")
print("Sample outputs:", sst2_results[:3])
print("Sample true labels:", true_labels[:3])