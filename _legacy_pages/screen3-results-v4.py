import json
import streamlit as st
import plotly.graph_objects as go

st.set_page_config(page_title="Discovery Lens", layout="wide")

RISK_COLOR = {"low": "#639922", "medium": "#EF9F27", "high": "#E24B4A"}

DEMO_OST = {
    "goal": "Help product teams at B2B SaaS companies turn raw discovery into prioritised action within one working day",
    "opportunities": [
        {
            "jtbd": "When I finish user interviews, I want to spot recurring themes quickly, so I can brief my team without spending a day in spreadsheets.",
            "cluster_id": 0, "importance": 0.42, "satisfaction": 0.27, "source_type_diversity": 0.75,
            "odi_score": 0.31, "evidence_robustness": 0.64, "priority_score": 0.44,
            "solutions": [
                {"label": "Auto-cluster on upload", "assumptions": [{"text": "Users upload consistently", "risk": "low"}]},
                {"label": "JTBD summary card", "assumptions": [{"text": "LLM output is reliable", "risk": "medium"}]},
                {"label": "AI synthesis report", "assumptions": [{"text": "Users trust AI output", "risk": "high"}]},
            ]
        },
        {
            "jtbd": "When I present findings to stakeholders, I want to show which quotes back each insight, so I can defend prioritisation decisions.",
            "cluster_id": 1, "importance": 0.35, "satisfaction": 0.40, "source_type_diversity": 0.50,
            "odi_score": 0.21, "evidence_robustness": 0.45, "priority_score": 0.31,
            "solutions": [
                {"label": "Quote traceability panel", "assumptions": [{"text": "Source map is complete", "risk": "low"}]},
                {"label": "Exportable evidence map", "assumptions": [{"text": "Export format is agreed", "risk": "medium"}]},
            ]
        },
        {
            "jtbd": "When I'm juggling multiple data sources, I want a single place to upload everything, so I can avoid stitching files manually.",
            "cluster_id": 2, "importance": 0.31, "satisfaction": 0.50, "source_type_diversity": 0.50,
            "odi_score": 0.16, "evidence_robustness": 0.43, "priority_score": 0.27,
            "solutions": [
                {"label": "Multi-file drag-drop", "assumptions": [{"text": "File formats are supported", "risk": "low"}]},
                {"label": "Source type tagging", "assumptions": [{"text": "Users tag correctly", "risk": "low"}]},
            ]
        },
        {
            "jtbd": "When I share an OST with my team, I want them to understand the scoring logic, so I can get buy-in without a long explanation.",
            "cluster_id": 3, "importance": 0.22, "satisfaction": 0.54, "source_type_diversity": 0.25,
            "odi_score": 0.10, "evidence_robustness": 0.24, "priority_score": 0.16,
            "solutions": [
                {"label": "Inline score tooltip", "assumptions": [{"text": "Tooltip is discoverable", "risk": "medium"}]},
                {"label": "JSON export", "assumptions": [{"text": "Team reads JSON", "risk": "low"}]},
            ]
        },
    ]
}

DEMO_SOURCE_MAP = {
    "interview_asana_03_007": {"text": "I usually end up copy-pasting into a giant Notion doc and then spending two days trying to find the common threads by hand.", "filename": "interview_asana_03.txt", "source_type": "interview", "cluster_id": 0},
    "g2_asana_019_002": {"text": "The hardest part of discovery isn't collecting data — it's making sense of it fast enough to be useful in sprint planning.", "filename": "g2_asana_019.csv", "source_type": "review", "cluster_id": 0},
    "interview_asana_01_012": {"text": "We have themes, but proving they're real to engineering always requires going back to every original note. It's exhausting.", "filename": "interview_asana_01.txt", "source_type": "interview", "cluster_id": 0},
    "ticket_asana_005_003": {"text": "Stakeholders keep asking me to justify my roadmap decisions — I need a way to show the evidence trail quickly.", "filename": "tickets_asana.csv", "source_type": "ticket", "cluster_id": 1},
    "interview_asana_02_008": {"text": "I spent three hours building a slide just to show why one feature matters more than another. There has to be a better way.", "filename": "interview_asana_02.txt", "source_type": "interview", "cluster_id": 1},
}

# ── DATA ──────────────────────────────────────────────────────────────────────
ost = st.session_state.get("ost") or DEMO_OST
source_map = st.session_state.get("source_map") or DEMO_SOURCE_MAP
product_name = st.session_state.get("product_name", "")
is_demo = not st.session_state.get("ost")

# Goal: prefer session_state (set by screen1 widget) over LLM JSON field
goal_display = st.session_state.get("goal", "") or ost.get("goal", "")

opportunities = ost.get("opportunities", [])

if "selected_opp" not in st.session_state:
    st.session_state["selected_opp"] = 0

# ── HEADER ────────────────────────────────────────────────────────────────────
col_title, col_export = st.columns([4, 1])
with col_title:
    if product_name:
        st.caption(f"Product · {product_name}")
    st.markdown("## Discovery results")
    if is_demo:
        st.caption("Showing demo data — run the pipeline on the upload screen to see your results.")
with col_export:
    st.download_button(
        label="Export JSON ↓",
        data=json.dumps(ost, indent=2),
        file_name="discovery_lens_ost.json",
        mime="application/json",
    )

st.divider()

# ── TABS ──────────────────────────────────────────────────────────────────────
tab_ost, tab_matrix, tab_heatmap = st.tabs(["OST tree", "Priority matrix", "Evidence heatmap"])

# ── TAB 1: OST TREE ───────────────────────────────────────────────────────────
with tab_ost:
    # Goal node
    st.markdown(
        f"""<div style="background:#EEEDFE;border:0.5px solid #AFA9EC;border-radius:12px;
        padding:12px 18px;display:inline-block;margin-bottom:16px;">
        <div style="font-size:11px;font-weight:500;color:#3C3489;text-transform:uppercase;
        letter-spacing:0.04em;margin-bottom:4px;">Product goal</div>
        <div style="font-size:14px;font-weight:500;color:#26215C;max-width:560px;">{goal_display}</div>
        </div>""",
        unsafe_allow_html=True,
    )

    st.markdown(
        "<div style='font-size:11px;font-weight:500;color:#888;text-transform:uppercase;"
        "letter-spacing:0.04em;margin-bottom:12px;'>Opportunities — click to see evidence</div>",
        unsafe_allow_html=True,
    )

    # Opportunity cards — 2 columns
    pairs = [opportunities[i:i+2] for i in range(0, len(opportunities), 2)]
    for pair in pairs:
        cols = st.columns(len(pair))
        for col, opp in zip(cols, pair):
            idx = opportunities.index(opp)
            is_selected = st.session_state["selected_opp"] == idx
            border = "#AFA9EC" if is_selected else "#E0DFDB"
            shadow = "box-shadow:0 0 0 2px #EEEDFE;" if is_selected else ""

            pills_html = ""
            for sol in opp.get("solutions", []):
                risk = sol.get("assumptions", [{}])[0].get("risk", "low")
                color = RISK_COLOR.get(risk, "#639922")
                pills_html += (
                    f'<span style="font-size:12px;background:#F4F4F2;border:0.5px solid #E0DFDB;'
                    f'border-radius:20px;padding:4px 10px;color:#5F5E5A;margin-right:4px;display:inline-block;">'
                    f'<span style="display:inline-block;width:7px;height:7px;border-radius:50%;'
                    f'background:{color};margin-right:4px;"></span>{sol["label"]}</span>'
                )

            priority_score = opp.get("priority_score") or 0
            odi_score = opp.get("odi_score") or 0
            evidence_robustness = opp.get("evidence_robustness") or 0
            importance = opp.get("importance") or 0
            satisfaction = opp.get("satisfaction") or 0

            if priority_score >= 0.35:
                priority_label, priority_bg, priority_color = "High", "#F7C1C1", "#A32D2D"
            elif priority_score >= 0.20:
                priority_label, priority_bg, priority_color = "Medium", "#FEF3CD", "#7A4F00"
            else:
                priority_label, priority_bg, priority_color = "Low", "#EAF3DE", "#27500A"

            with col:
                st.markdown(
                    f"""<div style="border:0.5px solid {border};border-radius:12px;
                    background:#fff;padding:12px 14px;margin-bottom:8px;{shadow}">
                    <div style="display:flex;justify-content:space-between;align-items:flex-start;gap:8px;margin-bottom:8px;">
                        <div style="font-size:13px;color:#1A1916;line-height:1.5;flex:1;">{opp["jtbd"]}</div>
                        <div style="text-align:right;">
                            <div style="font-size:20px;font-weight:500;color:#534AB7;">{priority_score:.2f}</div>
                            <div style="font-size:10px;color:#534AB7;">Priority score</div>
                            <div style="margin-top:6px;">
                                <span style="font-size:11px;font-weight:600;padding:3px 10px;border-radius:20px;
                                background:{priority_bg};color:{priority_color};">{priority_label}</span>
                            </div>
                        </div>
                    </div>
                    <div style="display:flex;gap:6px;flex-wrap:wrap;margin-bottom:10px;">
                        <span style="font-size:11px;padding:3px 8px;border-radius:4px;background:#E6F1FB;color:#0C447C;">ODI {odi_score:.2f}</span>
                        <span style="font-size:11px;padding:3px 8px;border-radius:4px;background:#EAF3DE;color:#27500A;">Robustness {evidence_robustness:.2f}</span>
                        <span style="font-size:11px;padding:3px 8px;border-radius:4px;background:#F1EFE8;color:#444441;">Imp {importance:.2f} · Sat {satisfaction:.2f}</span>
                    </div>
                    <div>{pills_html}</div>
                    </div>""",
                    unsafe_allow_html=True,
                )
                if st.button("View evidence", key=f"opp_btn_{idx}"):
                    st.session_state["selected_opp"] = idx
                    st.rerun()

    # Evidence panel
    st.divider()
    sel = st.session_state["selected_opp"]
    if sel < len(opportunities):
        selected_opp = opportunities[sel]
        selected_cid = selected_opp.get("cluster_id")
        st.markdown(
            f"<div style='font-size:11px;font-weight:500;color:#888;text-transform:uppercase;"
            f"letter-spacing:0.04em;margin-bottom:10px;'>Evidence — \"{selected_opp['jtbd'][:60]}…\"</div>",
            unsafe_allow_html=True,
        )
        evidence_chunks = [
            (cid, chunk) for cid, chunk in source_map.items()
            if str(chunk.get("cluster_id", "")) == str(selected_cid)
        ]

        # Debug expander — remove before demo
        with st.expander("🔍 Debug evidence lookup", expanded=False):
            st.write(f"**selected_cid:** `{selected_cid!r}` (type: `{type(selected_cid).__name__}`)")
            st.write(f"**source_map size:** {len(source_map)} entries")
            all_cids = sorted(set(str(c.get("cluster_id", "None")) for c in source_map.values()))
            st.write(f"**cluster_ids in source_map:** {all_cids}")
            st.write(f"**matches found:** {len(evidence_chunks)}")

        if evidence_chunks:
            ev_cols = st.columns(min(len(evidence_chunks), 3))
            for i, (cid, chunk) in enumerate(evidence_chunks[:3]):
                with ev_cols[i]:
                    st.markdown(
                        f"""<div style="border:0.5px solid #E0DFDB;border-radius:10px;
                        background:#fff;padding:12px 14px;">
                        <div style="font-size:11px;color:#888;margin-bottom:6px;">
                            <span style="background:#F1EFE8;color:#5F5E5A;font-size:10px;
                            padding:2px 6px;border-radius:3px;">{chunk.get("source_type","")}</span>
                            &nbsp;<span style="font-size:11px;color:#888;">{chunk.get("filename","")}</span>
                            &nbsp;<span style="font-size:10px;color:#B4B2A9;">{cid}</span>
                        </div>
                        <div style="font-size:13px;color:#1A1916;line-height:1.55;font-style:italic;">
                            "{chunk.get("text","")}"
                        </div>
                        </div>""",
                        unsafe_allow_html=True,
                    )
        else:
            st.caption("No evidence chunks linked to this opportunity yet.")

# ── TAB 2: PRIORITY MATRIX ───────────────────────────────────────────────────
with tab_matrix:
    if not opportunities:
        st.info("Run the pipeline to see the priority matrix.")
    else:
        col_chart, col_legend = st.columns([3, 2])
        with col_chart:
            fig = go.Figure()

            quadrants = [
                (0, 0.5, 0.5, 1, "#EEEDFE", "watch"),
                (0.5, 1, 0.5, 1, "#F7C1C1", "prioritise"),
                (0, 0.5, 0, 0.5, "#F1EFE8", "deprioritise"),
                (0.5, 1, 0, 0.5, "#EAF3DE", "maintain"),
            ]
            for x0, x1, y0, y1, color, label in quadrants:
                fig.add_shape(type="rect", x0=x0, x1=x1, y0=y0, y1=y1,
                              fillcolor=color, opacity=0.5, line_width=0)
                fig.add_annotation(x=(x0+x1)/2, y=(y0+y1)/2, text=label,
                                   showarrow=False, font=dict(size=11, color="#888"))

            for i, opp in enumerate(opportunities):
                score = opp.get("priority_score") or 0
                fig.add_trace(go.Scatter(
                    x=[opp.get("importance", 0)],
                    y=[opp.get("satisfaction", 0)],
                    mode="markers+text",
                    marker=dict(size=max(score * 60, 20), color="#534AB7",
                                opacity=0.4 + score * 0.6),
                    text=[str(i + 1)],
                    textposition="middle center",
                    textfont=dict(color="white", size=12),
                    hovertemplate=(
                        f"<b>Opp {i+1}</b><br>"
                        f"Importance: {opp.get('importance',0):.2f}<br>"
                        f"Satisfaction: {opp.get('satisfaction',0):.2f}<br>"
                        f"ODI score: {opp.get('odi_score',0):.2f}<br>"
                        f"Robustness: {opp.get('evidence_robustness',0):.2f}<br>"
                        f"Priority score: {score:.2f}<extra></extra>"
                    ),
                    showlegend=False,
                ))

            fig.update_layout(
                xaxis=dict(title="Importance →", range=[0, 1], showgrid=False),
                yaxis=dict(title="Satisfaction →", range=[0, 1], showgrid=False),
                plot_bgcolor="white",
                margin=dict(l=40, r=20, t=20, b=40),
                height=360,
            )
            fig.add_shape(type="line", x0=0.5, x1=0.5, y0=0, y1=1,
                          line=dict(color="#D3D1C7", width=1))
            fig.add_shape(type="line", x0=0, x1=1, y0=0.5, y1=0.5,
                          line=dict(color="#D3D1C7", width=1))
            st.plotly_chart(fig, use_container_width=True)

        with col_legend:
            st.markdown("**Opportunities by priority score**")
            for i, opp in enumerate(opportunities):
                score = opp.get("priority_score") or 0
                short = opp["jtbd"].split(",")[0].replace("When I ", "").capitalize()[:40]
                st.markdown(
                    f'<div style="display:flex;align-items:center;gap:8px;margin-bottom:8px;">'
                    f'<div style="width:10px;height:10px;border-radius:50%;background:#534AB7;'
                    f'opacity:{0.4+score*0.6};flex-shrink:0;"></div>'
                    f'<div style="font-size:12px;"><b>{i+1}</b> — {short}… ({score:.2f})</div>'
                    f'</div>',
                    unsafe_allow_html=True,
                )
            st.markdown(
                "<div style='margin-top:16px;font-size:11px;color:#888;line-height:1.7;'>"
                "Bubble size = priority score<br>"
                "X axis = importance (cluster size / total chunks)<br>"
                "Y axis = satisfaction ((sentiment+1)/2)<br>"
                "<b>Top-right = prioritise</b> · <b>Bottom-right = maintain</b>"
                "</div>",
                unsafe_allow_html=True,
            )

# ── TAB 3: EVIDENCE HEATMAP ───────────────────────────────────────────────────
with tab_heatmap:
    if not source_map:
        st.info("Run the pipeline to see the evidence heatmap.")
    else:
        st.caption("Chunk count per opportunity × source type. Wider bar = more evidence.")
        source_types = sorted({c.get("source_type", "") for c in source_map.values() if c.get("source_type")})
        bar_colors = ["#CECBF6", "#B5D4F4", "#9FE1CB", "#D3D1C7", "#F4C4A0", "#C4E0C4"]

        for i, opp in enumerate(opportunities):
            cid = opp.get("cluster_id")
            short = opp["jtbd"].split(",")[0][:55]
            st.markdown(f"**Opp {i+1} — {short}…**")

            chunks_for_opp = [c for c in source_map.values() if str(c.get("cluster_id", "")) == str(cid)]
            total = len(chunks_for_opp) or 1
            has_any = False
            for src in source_types:
                count = sum(1 for c in chunks_for_opp if c.get("source_type") == src)
                if count == 0:
                    continue
                has_any = True
                bar_pct = int((count / max(total, 1)) * 260)
                st.markdown(
                    f'<div style="display:flex;align-items:center;gap:8px;margin-bottom:6px;">'
                    f'<div style="font-size:12px;color:#888;width:120px;">{src.capitalize()}</div>'
                    f'<div style="height:20px;width:{max(bar_pct,30)}px;border-radius:3px;'
                    f'background:{bar_colors[i % len(bar_colors)]};display:flex;align-items:center;'
                    f'padding-left:6px;font-size:11px;color:#26215C;font-weight:500;">'
                    f'{count} chunk{"s" if count != 1 else ""}</div>'
                    f'</div>',
                    unsafe_allow_html=True,
                )
            if not has_any:
                st.caption("No evidence chunks linked yet.")
            st.markdown("---")
