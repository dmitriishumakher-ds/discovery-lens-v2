"""Page 1 — Goal Input"""
import streamlit as st

st.set_page_config(page_title="Set Goal — Discovery Lens", page_icon="🎯", layout="wide")
st.title("🎯 Set your product goal")
st.markdown("This goal will frame every opportunity and solution the tool surfaces. Be specific.")

with st.form("goal_form"):
    product_name = st.text_input("Product name", value=st.session_state.get("product_name", ""), placeholder="e.g. Asana, Revolut, Lidl Plus")
    goal = st.text_area("Goal statement", value=st.session_state.get("goal", ""), placeholder="e.g. Increase 30-day retention for new users on the mobile app", height=100)
    submitted = st.form_submit_button("Save goal and continue →")

if submitted:
    if not product_name.strip() or not goal.strip():
        st.error("Both fields are required.")
    else:
        st.session_state["product_name"] = product_name.strip()
        st.session_state["goal"] = goal.strip()
        st.success(f"Goal saved for **{product_name}**. Head to Upload to add your discovery files.")
