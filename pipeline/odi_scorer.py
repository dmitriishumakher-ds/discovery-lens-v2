"""
<<<<<<< asma-ui-only
odi_scorer.py — Clusters + chunks → three ODI scores (deterministic)
Owner: Asma

DATA CONTRACT (see docs/data_contracts.md / CLAUDE2.md):
    Input:  clusters (list[dict]), chunks (list[dict])
    Output: list of dicts sorted by priority_score descending

Scores:
    importance          = cluster_size / total_chunks
    avg_sentiment       = mean VADER compound score across chunks in cluster
    satisfaction        = (avg_sentiment + 1) / 2
    source_type_diversity = unique source types in cluster / total unique source types
    odi_score           = importance * (1 - satisfaction)
    evidence_robustness = (source_type_diversity * 0.65) + (importance * 0.35)
    priority_score      = (odi_score * 0.60) + (evidence_robustness * 0.40)
"""

from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer


def score(clusters: list[dict], chunks: list[dict]) -> list[dict]:
    analyser = SentimentIntensityAnalyzer()
    chunk_map = {c["chunk_id"]: c for c in chunks}
    total_chunks = len(chunks)
    all_source_types = {c.get("source_type", "") for c in chunks if c.get("source_type")}
    total_source_types = max(len(all_source_types), 1)

    scored = []
    for cl in clusters:
        chunk_ids = cl.get("all_chunk_ids", [])
        cluster_chunks = [chunk_map[cid] for cid in chunk_ids if cid in chunk_map]
        cluster_size = len(cluster_chunks)

        sentiments = [analyser.polarity_scores(c["text"])["compound"] for c in cluster_chunks]
        avg_sentiment = sum(sentiments) / len(sentiments) if sentiments else 0.0

        source_types_in_cluster = {c.get("source_type", "") for c in cluster_chunks if c.get("source_type")}
        source_type_diversity = len(source_types_in_cluster) / total_source_types

        importance = cluster_size / total_chunks if total_chunks > 0 else 0.0
        satisfaction = (avg_sentiment + 1) / 2
        odi_score = importance * (1 - satisfaction)
        evidence_robustness = (source_type_diversity * 0.65) + (importance * 0.35)
        priority_score = (odi_score * 0.60) + (evidence_robustness * 0.40)

        scored.append({
            "cluster_id": cl["cluster_id"],
            "cluster_size": cluster_size,
            "importance": round(importance, 4),
            "avg_sentiment": round(avg_sentiment, 4),
            "satisfaction": round(satisfaction, 4),
            "source_type_diversity": round(source_type_diversity, 4),
            "odi_score": round(odi_score, 4),
            "evidence_robustness": round(evidence_robustness, 4),
            "priority_score": round(priority_score, 4),
        })

    return sorted(scored, key=lambda x: x["priority_score"], reverse=True)
=======
odi_scorer.py
Computes deterministic ODI priority signals per cluster.
No LLM. No external API. Pure VADER + cluster metadata.

Input:
    clusters  — output of clusterer.py
    chunks    — output of chunker.py (used to resolve text + compute sentiment)

Output:
    list of scored cluster dicts (see data contract in docs/data_contracts.md)
"""

from nltk.sentiment.vader import SentimentIntensityAnalyzer
from typing import Any

# Initialise once at module level — avoids reloading the lexicon on every call
_vader = SentimentIntensityAnalyzer()


def score_clusters(
    clusters: list[dict[str, Any]],
    chunks: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    Score each cluster using importance and satisfaction proxies.

    importance    = cluster_size / total_chunks
    satisfaction  = (avg_vader_compound + 1) / 2   # normalised to 0–1
    opportunity   = importance * (1 - satisfaction)

    Args:
        clusters: output of clusterer.py
        chunks:   output of chunker.py

    Returns:
        list of scored cluster dicts, same order as input clusters
    """
    # Build a lookup from chunk_id → text for fast access
    chunk_text: dict[str, str] = {c["chunk_id"]: c["text"] for c in chunks}
    total_chunks: int = len(chunks)

    if total_chunks == 0:
        raise ValueError("chunks list is empty — cannot compute importance scores")

    scored: list[dict[str, Any]] = []

    for cluster in clusters:
        cluster_id: int = cluster["cluster_id"]
        chunk_ids: list[str] = cluster["all_chunk_ids"]
        cluster_size: int = len(chunk_ids)

        # --- Importance ---
        importance: float = cluster_size / total_chunks

        # --- Sentiment (VADER compound per chunk, then average) ---
        compound_scores: list[float] = []
        for cid in chunk_ids:
            text = chunk_text.get(cid)
            if text:
                score = _vader.polarity_scores(text)["compound"]
                compound_scores.append(score)

        if compound_scores:
            avg_sentiment: float = sum(compound_scores) / len(compound_scores)
        else:
            avg_sentiment = 0.0  # neutral fallback if no text found

        # --- Satisfaction (normalise VADER -1…1 → 0…1) ---
        satisfaction: float = (avg_sentiment + 1) / 2

        # --- Opportunity score ---
        opportunity_score: float = importance * (1 - satisfaction)

        scored.append(
            {
                "cluster_id": cluster_id,
                "cluster_size": cluster_size,
                "importance": round(importance, 4),
                "avg_sentiment": round(avg_sentiment, 4),
                "satisfaction": round(satisfaction, 4),
                "opportunity_score": round(opportunity_score, 4),
            }
        )

    # Sort highest opportunity first — convenient for results page
    scored.sort(key=lambda x: x["opportunity_score"], reverse=True)
    return scored
>>>>>>> main
