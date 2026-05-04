# test_pipeline_headless.py
"""
End-to-end headless pipeline test — no Streamlit, no UI.
Usage:
  python test_pipeline_headless.py --data_dir data/synthetic/revolut --goal "Help Revolut users manage their money more confidently"
"""

import argparse
import json
import os
import sys
from pathlib import Path

# Add repo root to path so pipeline imports work
sys.path.insert(0, str(Path(__file__).parent))

from pipeline.chunker import chunk_text as chunk
from pipeline.embedder import embed
from pipeline.clusterer import cluster
from pipeline.odi_scorer import score

# source_map.py may still be in progress
try:
    from pipeline.source_map import build_source_map
    HAS_SOURCE_MAP = True
except ImportError:
    HAS_SOURCE_MAP = False
    print("⚠️  source_map.py not found — skipping source_map step")

from pipeline.llm import generate_ost

# ── helpers ──────────────────────────────────────────────────────────────────

SOURCE_TYPE_MAP = {
    "interview": "interview",
    "usability": "usability",
    "ticket":    "ticket",
    "review":    "review",
}

def infer_source_type(filename: str) -> str:
    """Infer source_type from filename. Falls back to 'review'."""
    fname = filename.lower()
    for key in SOURCE_TYPE_MAP:
        if key in fname:
            return key
    return "review"

def load_files(data_dir: str) -> list[dict]:
    """Load all .txt / .md files from data_dir as raw text dicts."""
    files = []
    for path in sorted(Path(data_dir).rglob("*")):
        if path.suffix in (".txt", ".md") and path.is_file():
            raw_text = path.read_text(encoding="utf-8", errors="ignore")
            files.append({
                "filename": path.name,
                "source_type": infer_source_type(path.name),
                "raw_text": raw_text,
            })
    if not files:
        sys.exit(f"No .txt or .md files found in {data_dir}")
    print(f"✅ Loaded {len(files)} files from {data_dir}")
    return files

# ── pipeline steps ────────────────────────────────────────────────────────────

def run_pipeline(files: list[dict], goal: str) -> dict:
    # 1. Chunking
    all_chunks = []
    for f in files:
        chunks = chunk(f["raw_text"], f["filename"], f["source_type"])
        all_chunks.extend(chunks)
    print(f"✅ chunker   → {len(all_chunks)} chunks")
    assert all_chunks, "chunker returned 0 chunks"
    assert all(k in all_chunks[0] for k in ("chunk_id", "text", "filename", "source_type")), \
        "chunk dict missing required keys"

    # 2. Embeddings
    embeddings = embed(all_chunks)
    print(f"✅ embedder  → embeddings shape {embeddings.shape}")
    assert embeddings.shape == (len(all_chunks), 384), \
        f"Expected ({len(all_chunks)}, 384), got {embeddings.shape}"

    # 3. Clustering
    clusters = cluster(all_chunks, embeddings)
    print(f"✅ clusterer → {len(clusters)} clusters")
    assert clusters, "clusterer returned 0 clusters"
    assert all(k in clusters[0] for k in ("cluster_id", "representative_chunks", "all_chunk_ids")), \
        "cluster dict missing required keys"

    # 4. source_map (optional — may be in progress)
    source_map = {}
    if HAS_SOURCE_MAP:
        source_map = build_source_map(all_chunks, clusters)
        print(f"✅ source_map → {len(source_map)} entries")
    else:
        print("⏭️  source_map skipped")

    # 5. ODI scoring
    scored_clusters = score(clusters, all_chunks)
    print(f"✅ odi_scorer → {len(scored_clusters)} scored clusters")
    required_score_keys = ("cluster_id", "odi_score", "evidence_robustness", "priority_score",
                           "importance", "satisfaction", "source_type_diversity")
    assert all(k in scored_clusters[0] for k in required_score_keys), \
        f"scored_cluster missing keys. Got: {list(scored_clusters[0].keys())}"
    # Verify sort order
    scores = [sc["priority_score"] for sc in scored_clusters]
    assert scores == sorted(scores, reverse=True), "scored_clusters not sorted by priority_score desc"

    # 6. LLM → OST
    ost = generate_ost(clusters, scored_clusters, goal)
    print(f"✅ llm.py    → OST with {len(ost.get('opportunities', []))} opportunities")

    return {"chunks": all_chunks, "clusters": clusters, "scored_clusters": scored_clusters,
            "source_map": source_map, "ost": ost}

# ── validation ────────────────────────────────────────────────────────────────

def validate_ost(ost: dict, scored_clusters: list[dict]):
    print("\n── OST validation ──────────────────────────────────────────")
    scored_ids = {sc["cluster_id"] for sc in scored_clusters}
    issues = []

    for i, opp in enumerate(ost.get("opportunities", [])):
        # JTBD format
        jtbd = opp.get("jtbd", "")
        if not (jtbd.startswith("When I") and "I want to" in jtbd and "so I can" in jtbd):
            issues.append(f"  opp[{i}] JTBD format wrong: {jtbd[:80]}")

        # Score fields injected (not null) if cluster_id is known
        cid = opp.get("cluster_id")
        if cid in scored_ids:
            for field in ("odi_score", "evidence_robustness", "priority_score"):
                if opp.get(field) is None:
                    issues.append(f"  opp[{i}] cluster_id={cid}: {field} is null despite match in scored_clusters")

        # Solutions present
        if not opp.get("solutions"):
            issues.append(f"  opp[{i}] has no solutions")

        # Risk values valid
        for sol in opp.get("solutions", []):
            for assumption in sol.get("assumptions", []):
                if assumption.get("risk") not in ("low", "medium", "high"):
                    issues.append(f"  opp[{i}] assumption has invalid risk: {assumption.get('risk')}")

    if issues:
        print("❌ Validation issues found:")
        for issue in issues:
            print(issue)
    else:
        print("✅ All OST validation checks passed")

    return len(issues) == 0

# ── main ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--data_dir", default="data/synthetic/revolut",
                        help="Directory containing synthetic .txt/.md files")
    parser.add_argument("--goal", default="Help Revolut users manage their money more confidently",
                        help="Product goal string")
    parser.add_argument("--output", default="test_output_ost.json",
                        help="Path to write the final OST JSON for inspection")
    args = parser.parse_args()

    print(f"\n🔬 Discovery Lens — headless pipeline test")
    print(f"   data_dir : {args.data_dir}")
    print(f"   goal     : {args.goal}\n")

    files = load_files(args.data_dir)
    results = run_pipeline(files, args.goal)
    passed = validate_ost(results["ost"], results["scored_clusters"])

    # Write OST to disk for manual inspection
    with open(args.output, "w") as f:
        json.dump(results["ost"], f, indent=2)
    print(f"\n📄 OST written to {args.output}")

    sys.exit(0 if passed else 1)