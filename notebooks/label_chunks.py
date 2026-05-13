import pandas as pd
import os

os.chdir(os.path.expanduser("~/capstone/discovery-lens"))

df = pd.read_csv("notebooks/chunks_for_labelling_sample.csv")
df["label"] = df["label"].astype(str).replace("nan", "")
VALID = {"p": "positive", "n": "negative", "u": "neutral"}

for i, row in df.iterrows():
    if pd.notna(row["label"]):
        continue  # skip already labelled

    print(f"\n--- {i+1}/60 | {row['source_type']} | {row['chunk_id']} ---")
    print(row["text"])
    print()

    while True:
        choice = input("Label [p=positive / n=negative / u=neutral / q=quit]: ").strip().lower()
        if choice == "q":
            df.to_csv("notebooks/chunks_for_labelling_sample.csv", index=False)
            print("Saved and quit.")
            exit()
        if choice in VALID:
            df.at[i, "label"] = VALID[choice]
            df.to_csv("notebooks/chunks_for_labelling_sample.csv", index=False)
            break
        print("Invalid input — use p, n, u, or q")

print("\nAll done!")
df.to_csv("notebooks/chunks_for_labelling_sample.csv", index=False)
print(df["label"].value_counts())