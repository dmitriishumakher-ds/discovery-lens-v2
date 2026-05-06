import streamlit as st

# ── PAGE CONFIG ────────────────────────────────────────────────
# This must be the FIRST Streamlit command in the file.
# It sets the browser tab title and the page layout.
st.set_page_config(
    page_title="Discovery Lens",
    layout="centered"   # keeps content in a readable column
)

# ── SESSION STATE SETUP ────────────────────────────────────────
# st.session_state is like a shared memory that persists across
# all 3 screens. We initialise the keys here so they always exist,
# even before the user has typed anything.
if "product_name" not in st.session_state:
    st.session_state["product_name"] = ""

if "goal" not in st.session_state:
    st.session_state["goal"] = ""

if "current_screen" not in st.session_state:
    st.session_state["current_screen"] = 1   # start on Screen 1

# ── STEPPER UI ─────────────────────────────────────────────────
# Shows the user where they are in the 3-step flow.
# We use st.columns to put the 3 steps side by side.
st.markdown("---")
col1, col2, col3 = st.columns(3)

with col1:
    # Screen 1 is the current screen — highlight it
    st.markdown("**① Goal** ← you are here")
with col2:
    st.markdown("② Upload")
with col3:
    st.markdown("③ Results")

st.markdown("---")

# ── SCREEN 1 CONTENT ───────────────────────────────────────────
st.title("Define your product goal")
st.caption(
    "This goal will be passed into every AI prompt to frame the analysis."
)
#adding the star(required entry)
st.markdown("<small style='color: gray;'>* required field</small>", unsafe_allow_html=True)
# st.text_input renders a single-line text box.
# The first argument is the label shown above the box.
# `value` pre-fills it with whatever is already saved in session state
# (so if the user goes back from Screen 2, their input is still there).
product_name = st.text_input(
    label="Product name *",
     key="product_name",
    placeholder="e.g. Asana"
)

# st.text_area renders a multi-line text box.
# `height` controls how tall it is in pixels.
goal_statement = st.text_area(
    label="Goal statement *",
    key="goal",
    placeholder=(
        "e.g. Increase the percentage of new teams that complete "
        "their first project within 30 days of signing up"
    ),
    height=120
)

# ── NEXT BUTTON ────────────────────────────────────────────────
# st.button returns True only in the moment the user clicks it.
# use_container_width=True makes the button stretch full width.
if st.button("Next: upload files →", use_container_width=True, type="primary"):

    # Validate: both fields must be filled before moving on
    if not product_name.strip():
        # st.error shows a red error box
        st.error("Please enter a product name before continuing.")

    elif not goal_statement.strip():
        st.error("Please enter a goal statement before continuing.")

    else:
        st.session_state["current_screen"] = 2
        st.switch_page("pages/screen2_upload-v2.py")

# ── PREVIEW (helpful while building) ──────────────────────────
# This shows you what is currently saved in session state.
# Delete this block once you are happy with Screen 1.
with st.expander("🔍 Debug: session state (delete before demo)"):
    st.json({
        "product_name": st.session_state["product_name"],
        "goal": st.session_state["goal"],
        "current_screen": st.session_state["current_screen"]
    })
