"""Page 3 — Results"""
import streamlit as st

st.set_page_config(page_title="Results — Discovery Lens", page_icon="🌳", layout="wide")
st.title("🌳 Opportunity-Solution Tree")

if not st.session_state.get("ost"):
    st.warning("No OST yet. Upload your discovery files and run the pipeline first.")
    st.stop()

st.markdown(f"**Goal:** {st.session_state['ost'].get('goal', '')}")
st.divider()

tab1, tab2, tab3, tab4 = st.tabs(["OST Tree", "Priority Matrix", "Evidence Heatmap", "Assumptions"])
with tab1:
    st.info("OST tree component — Week 2")
with tab2:
    st.info("Priority matrix — Week 2")
with tab3:
    st.info("Evidence heatmap — Week 2")
with tab4:
    st.info("Assumption risk register — Week 2")
