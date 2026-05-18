import streamlit as st
from pipeline.extractor import extract
from pipeline.chunker import chunk
from pipeline.embedder import embed
from pipeline.clusterer import cluster
from pipeline.odi_scorer import score
from pipeline.llm import build_ost

st.set_page_config(
    page_title="Discovery Lens",
    layout="centered"
)

# Goal pill — show if available
goal = st.session_state.get("goal", "")
if goal:
    st.markdown(
        f'<div style="background:#f0f2f6;padding:8px 14px;border-radius:20px;display:inline-block;font-size:0.85rem;">🎯 {goal}</div>',
        unsafe_allow_html=True
    )

st.title("Upload your discovery data")
st.caption("Supported formats: PDF, TXT, CSV, DOCX · Max 500 chunks total")

st.divider()

SOURCE_TYPES = ["context", "discovery"]

SOURCE_DESCRIPTIONS = {
    "context": "Background material — market research, competitive analysis, internal docs",
    "discovery": "Primary research — interviews, usability tests, reviews, support tickets",
}

uploaded_files = st.file_uploader(
    "Drop your files here",
    type=["pdf", "txt", "csv", "docx"],
    accept_multiple_files=True
)

if uploaded_files:
    st.subheader("Set source type per file")
    file_configs = []
    for f in uploaded_files:
        col1, col2 = st.columns([2, 1])
        with col1:
            st.markdown(f"**{f.name}**")
        with col2:
            source_type = st.selectbox(
                "Type",
                SOURCE_TYPES,
                key=f"source_{f.name}",
                label_visibility="collapsed"
            )
        st.caption(SOURCE_DESCRIPTIONS[source_type])
        file_configs.append({"file": f, "source_type": source_type})

    st.divider()
    if st.button("Run analysis →", type="primary"):
        goal = st.session_state.get("goal", "")

        try:
            with st.status("Running analysis…", expanded=True) as status:

                st.write("Extracting text from files…")
                all_chunks = []
                for fc in file_configs:
                    raw_text = extract(fc["file"], fc["source_type"])
                    file_chunks = chunk(raw_text, fc["file"].name, fc["source_type"])
                    all_chunks.extend(file_chunks)
                st.session_state["chunks"] = all_chunks
                st.write(f"✓ {len(all_chunks)} chunks extracted")

                st.write("Embedding chunks…")
                embeddings = embed(all_chunks)
                st.session_state["embeddings"] = embeddings
                st.write(f"✓ Embeddings shape: {embeddings.shape}")

                st.write("Clustering…")
                clusters = cluster(all_chunks, embeddings)
                st.session_state["clusters"] = clusters
                st.write(f"✓ {len(clusters)} clusters found")

                st.write("Scoring opportunities…")
                scored_clusters = score(clusters, all_chunks)
                st.session_state["scored_clusters"] = scored_clusters
                st.write(f"✓ Scored {len(scored_clusters)} clusters")

                st.write("Building OST with Groq LLM…")
                ost = build_ost(clusters, scored_clusters, goal)
                st.session_state["ost"] = ost
                st.write(f"✓ OST built — {len(ost.get('opportunities', []))} opportunities")

                # Build source_map: chunk_id → {text, filename, source_type, cluster_id}
                chunk_to_cluster = {}
                for cl in clusters:
                    for cid in cl.get("all_chunk_ids", []):
                        chunk_to_cluster[cid] = cl["cluster_id"]
                source_map = {
                    c["chunk_id"]: {
                        "text": c["text"],
                        "filename": c["filename"],
                        "source_type": c["source_type"],
                        "cluster_id": int(chunk_to_cluster[c["chunk_id"]]) if c["chunk_id"] in chunk_to_cluster else None,
                    }
                    for c in all_chunks
                }
                st.session_state["source_map"] = source_map

                status.update(label="Analysis complete!", state="complete")

            st.switch_page("pages/screen3-results-v4.py")

        except Exception as e:
            st.error(f"Pipeline error: {e}")
