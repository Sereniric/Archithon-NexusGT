import sys
from pathlib import Path

import pandas as pd
import streamlit as st


PS01_ROOT = Path(__file__).resolve().parents[1]
if str(PS01_ROOT) not in sys.path:
    sys.path.insert(0, str(PS01_ROOT))

from backend.analyzer.apk_extractor import APKExtractionError, extract_manifest_from_apk
from backend.analyzer.manifest_parser import ManifestParseError, extract_permissions
from backend.analyzer.permission_analyzer import KnowledgeBaseError, analyze_permissions
from backend.analyzer.policy_analyzer import PolicyAnalysisError, analyze_policy_text
from backend.analyzer.app_purpose_analyzer import analyze_application_purpose
from backend.analyzer.purpose_analyzer import compare_permissions_with_policy
from backend.reporting.report_generator import generate_report_markdown, generate_report_json


st.set_page_config(
    page_title="Privacy and Permission Analyzer",
    page_icon="🔒",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
:root { --navy:#0b1f3a; --blue:#315cf6; --text:#111827; --slate:#687386; --surface:#ffffff; --canvas:#eaf0f7; --border:#e6eaf0; }
html, body, [class*="css"] { font-family: Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; color:var(--text); }
[data-testid="stAppViewContainer"] { background: var(--canvas); color:var(--text); }
[data-testid="stHeader"] { background: transparent; height:0; }
[data-testid="stToolbar"], [data-testid="stDecoration"] { visibility:hidden; height:0; }
[data-testid="stSidebar"] { background: var(--navy); border-right: none; min-width:280px !important; }
[data-testid="stSidebarContent"] { padding-top:1.25rem; }
[data-testid="stSidebarCollapseButton"] { color:white; }
[data-testid="stSidebar"] * { color: #eaf1fb !important; }
[data-testid="stSidebar"] hr { border-color: rgba(255,255,255,.12); }
.block-container { max-width:1180px; padding-top:1.25rem; padding-left:2rem; padding-right:2rem; padding-bottom:3rem; color:var(--text); }
[data-testid="stAppViewContainer"] h1, [data-testid="stAppViewContainer"] h2, [data-testid="stAppViewContainer"] h3,
[data-testid="stAppViewContainer"] label, [data-testid="stAppViewContainer"] p { color:var(--text); }
.hero { background:#ffffff; border:1px solid var(--border); border-radius:16px; padding:22px 26px; margin-bottom:16px; box-shadow:0 6px 18px rgba(15,35,70,.055); }
.hero h1 { color:var(--text); font-size:1.8rem; line-height:1.15; margin:0 0 7px 0; letter-spacing:-.025em; }
.hero p { color:var(--slate); margin:0; font-size:1rem; }
.section-heading { color:var(--text); font-size:1.35rem; font-weight:700; margin-bottom:.25rem; }
.section-copy { color:var(--slate); margin-bottom:1rem; }
.card { background:#ffffff; border:1px solid var(--border); border-radius:14px; padding:18px 20px; margin-bottom:12px; box-shadow:0 4px 14px rgba(15,35,70,.035); color:var(--text); }
.card h3 { color:var(--text); font-size:1rem; margin-top:0; }
.card p { color:var(--slate); }
[data-testid="stFileUploader"] { border:1px dashed #b8c7dc; border-radius:14px; background:#ffffff; padding:12px; }
[data-testid="stFileUploaderDropzone"] { min-height:120px; justify-content:center; border:0; }
[data-testid="stDataFrame"] { border:1px solid var(--border); border-radius:12px; overflow:hidden; }
[data-testid="stRadio"] > div { gap:8px; }
.stAlert { border-radius:12px; }
.workflow { display:grid; grid-template-columns:repeat(4,1fr); gap:12px; margin-top:16px; }
.workflow-step { background:#ffffff; border:1px solid var(--border); border-radius:12px; padding:16px; min-height:110px; color:var(--slate); }
.workflow-step strong { display:block; color:var(--text); margin-bottom:6px; }
.warning-card { border-left:4px solid #e6a23c; }
.success-card { border-left:4px solid #159b72; }
[data-testid="metric-container"] { background:#ffffff; border:1px solid var(--border); border-radius:14px; padding:16px; box-shadow:0 4px 14px rgba(15,35,70,.025); color:var(--text); }
[data-testid="stMetricLabel"] { color:var(--slate) !important; }
[data-testid="stMetricValue"] { color:var(--text) !important; }
.stButton button, .stDownloadButton button { border-radius:9px; font-weight:650; min-height:42px; color:var(--text); }
button[kind="primary"] { background:#315cf6 !important; border:1px solid #315cf6 !important; color:white !important; }
button[kind="primary"]:hover { background:#2348d3 !important; border-color:#2348d3 !important; }
[data-testid="stForm"] { border:1px solid var(--border); border-radius:14px; background:#ffffff; padding:18px; color:var(--text); }
@media (max-width:1100px) { [data-testid="stSidebar"] { min-width:260px !important; } .block-container { padding-left:1rem; padding-right:1rem; } .hero { width:auto; padding:18px 20px; } .hero h1 { font-size:1.55rem; } }
@media (max-width:800px) { .workflow { grid-template-columns:1fr; } .block-container { padding-left:.75rem; padding-right:.75rem; } .hero h1 { font-size:1.45rem; } }
</style>
""", unsafe_allow_html=True)

with st.sidebar:
    st.markdown("## 🔐 Archithon")
    st.markdown("### Privacy & Permission Analyzer")
    st.caption("Evidence-led review of declared Android permissions and supplied policy statements.")
    st.divider()
    page = st.radio(
        "Navigate",
        ["Overview", "Analysis inputs", "Permissions", "Privacy policy", "Transparency comparison", "Purpose review", "Reports"],
        key="navigation",
        label_visibility="collapsed",
    )
    st.divider()
    with st.expander("About & limitations"):
        st.write("PS01 is a deterministic analysis prototype. It does not install applications, execute APK code, scan devices, or establish actual runtime behavior.")
        st.write("Missing policy statements are potential transparency gaps—not proof of wrongdoing.")


def metric_row(permission_analysis=None, policy_analysis=None, comparison=None):
    permission_analysis = permission_analysis or st.session_state.get("permission_analysis")
    policy_analysis = policy_analysis or st.session_state.get("policy_analysis")
    comparison = comparison or st.session_state.get("policy_comparison")
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Permissions", permission_analysis["total"] if permission_analysis else 0)
    c2.metric("Recognized", len(permission_analysis["recognized"]) if permission_analysis else 0)
    c3.metric("Unknown", len(permission_analysis["unknown"]) if permission_analysis else 0)
    c4.metric("Policy topics", policy_analysis["mentioned_topics"] if policy_analysis else 0)
    c5.metric("Transparency gaps", comparison["gap_count"] if comparison else 0)


def render_header(title, copy):
    st.markdown(f'<div class="hero"><h1>{title}</h1><p>{copy}</p></div>', unsafe_allow_html=True)


if page == "Overview":
    render_header(
        "Application Privacy & Permission Analyzer",
        "Review Android declarations, policy evidence, transparency gaps, and stated purpose in one explainable workflow.",
    )
    metric_row()
    primary_left, primary_right = st.columns([2, 3])
    if primary_left.button("Start analysis", type="primary", use_container_width=True):
        st.session_state["navigation"] = "Analysis inputs"
        st.rerun()

    st.markdown("### Analysis workflow")
    workflow_items = [
        ("1 · Upload", "Choose an AndroidManifest.xml or APK file."),
        ("2 · Explain", "Map declarations to curated permission knowledge."),
        ("3 · Compare", "Match permissions with supplied policy and purpose evidence."),
        ("4 · Report", "Download traceable Markdown or JSON results."),
    ]
    for index in range(0, 4, 2):
        workflow_row = st.columns(2)
        for column, (title, copy) in zip(workflow_row, workflow_items[index:index + 2]):
            with column:
                st.markdown(f'<div class="workflow-step"><strong>{title}</strong>{copy}</div>', unsafe_allow_html=True)

    st.markdown("### Analysis status")
    status_columns = st.columns(3)
    if st.session_state.get("permission_analysis"):
        status_columns[0].success("Manifest ready")
    else:
        status_columns[0].info("Manifest not analyzed")
    if st.session_state.get("policy_analysis"):
        status_columns[1].success("Policy analyzed")
    else:
        status_columns[1].info("Policy not analyzed")
    if st.session_state.get("purpose_result"):
        status_columns[2].success("Purpose review available")
    else:
        status_columns[2].info("Purpose review optional")
    st.markdown('<div class="card warning-card"><h3>Evidence boundary</h3><p>Declared permissions indicate requested capabilities. They do not prove that sensitive data was accessed or that any data practice occurred.</p></div>', unsafe_allow_html=True)

elif page == "Analysis inputs":
    render_header("Analysis inputs", "Provide the evidence you want to review. All files are processed locally within the Streamlit session.")

    st.markdown("<div class='section-heading'>1 · Application manifest</div><div class='section-copy'>Upload one Android manifest or APK. Maximum APK size: 50 MB.</div>", unsafe_allow_html=True)
    manifest_source = st.radio("Manifest format", ["AndroidManifest.xml", "APK"], horizontal=True)
    uploaded_file = st.file_uploader(
        "Upload application file",
        type=["xml"] if manifest_source == "AndroidManifest.xml" else ["apk"],
        key="manifest_upload",
    )

    if uploaded_file is not None:
        try:
            with st.spinner("Validating and analyzing the application file…"):
                if manifest_source == "APK":
                    manifest_content = extract_manifest_from_apk(uploaded_file.getvalue())
                    st.session_state["manifest_source_name"] = "APK"
                else:
                    manifest_content = uploaded_file.getvalue()
                    st.session_state["manifest_source_name"] = "AndroidManifest.xml"
                permissions = extract_permissions(manifest_content)
                analysis = analyze_permissions(permissions)
        except (ManifestParseError, APKExtractionError, KnowledgeBaseError) as exc:
            st.error(str(exc))
        except Exception:
            st.error("The application file could not be read safely. Please verify the XML or APK and try again.")
        else:
            st.session_state["permission_analysis"] = analysis
            st.session_state.pop("policy_comparison", None)
            st.session_state.pop("purpose_result", None)
            st.markdown('<div class="card success-card"><h3>Manifest analysis complete</h3><p>Permission declarations were extracted and matched without claiming actual runtime behavior.</p></div>', unsafe_allow_html=True)

    st.divider()
    st.markdown("<div class='section-heading'>2 · Privacy policy</div><div class='section-copy'>Paste text or upload a TXT file. Neither source is treated as evidence of actual behavior.</div>", unsafe_allow_html=True)
    policy_file = st.file_uploader("Upload privacy policy (.txt)", type=["txt"], key="policy_upload")
    policy_text = st.text_area("Or paste privacy-policy text", height=180, key="policy_text")

    if st.button("Analyze privacy policy", type="primary"):
        supplied_text = policy_text if policy_text.strip() else (policy_file.getvalue() if policy_file else None)
        if supplied_text is None or (isinstance(supplied_text, bytes) and not supplied_text.strip()) or (isinstance(supplied_text, str) and not supplied_text.strip()):
            st.warning("Please provide policy text or upload a TXT file.")
        else:
            try:
                with st.spinner("Extracting grounded policy topics and excerpts…"):
                    policy_analysis = analyze_policy_text(supplied_text)
                st.session_state["policy_analysis"] = policy_analysis
                st.session_state.pop("policy_comparison", None)
                st.success("Privacy policy analysis complete.")
            except PolicyAnalysisError as exc:
                st.error(str(exc))

    st.divider()
    st.markdown("<div class='section-heading'>3 · Stated application purpose</div><div class='section-copy'>Optional context used only to highlight review questions.</div>", unsafe_allow_html=True)
    application_name = st.text_input("Application name (optional)", key="application_name")
    application_purpose = st.text_area("Application purpose or description (optional)", height=120, key="application_purpose")

    if st.button("Analyze stated purpose"):
        permission_analysis = st.session_state.get("permission_analysis")
        if permission_analysis is None:
            st.warning("Upload and analyze an AndroidManifest.xml file or APK before purpose review.")
        elif not application_name.strip() and not application_purpose.strip():
            st.warning("Enter an application name or purpose before running this optional review.")
        else:
            with st.spinner("Comparing stated purpose with known permission capabilities…"):
                purpose_result = analyze_application_purpose(application_name, application_purpose, permission_analysis)
            st.session_state["purpose_result"] = purpose_result
            st.success("Purpose review complete.")

elif page == "Permissions":
    render_header("Extracted permissions", "Review exact declarations, curated explanations, and unsupported identifiers.")
    analysis = st.session_state.get("permission_analysis")
    if not analysis:
        st.info("Upload and analyze a manifest or APK in Analysis inputs to view results.")
    else:
        c1, c2, c3 = st.columns(3)
        c1.metric("Total detected", analysis["total"])
        c2.metric("Recognized", len(analysis["recognized"]))
        c3.metric("Unknown / unsupported", len(analysis["unknown"]))

        if analysis["recognized"]:
            st.markdown("### Recognized permissions")
            rows = [{
                "Permission identifier": r["permission"],
                "Capability": r["capability"],
                "Protection level": r["protection_level"],
            } for r in analysis["recognized"]]
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
            for record in analysis["recognized"]:
                with st.expander(record["permission"]):
                    st.write(record["description"])
                    st.markdown(f"**Capability:** {record['capability']}")
                    st.markdown(f"**Potential privacy implications:** {record['privacy_implications']}")
                    st.markdown(f"**Protection level:** {record['protection_level']}")
                    if record["official_documentation_url"] != "Not available":
                        st.markdown(f"[Official Android documentation]({record['official_documentation_url']})")
                    st.caption("A declaration does not prove actual app behavior or data access.")

        if analysis["unknown"]:
            st.markdown("### Unknown / unsupported permissions")
            st.warning("These identifiers are preserved exactly and were not assigned speculative explanations.")
            st.dataframe(pd.DataFrame([{"Permission identifier": r["permission"], "Status": r["status"]} for r in analysis["unknown"]]), use_container_width=True, hide_index=True)

        if analysis["total"] == 0:
            st.info("No permission declarations were found in the supplied manifest.")

elif page == "Privacy policy":
    render_header("Privacy policy findings", "Deterministic topic extraction with original supporting excerpts.")
    policy = st.session_state.get("policy_analysis")
    if not policy:
        st.info("Provide policy text or upload a TXT policy in Analysis inputs.")
    else:
        c1, c2 = st.columns(2)
        c1.metric("Topics mentioned", policy["mentioned_topics"])
        c2.metric("Topics not mentioned or not determined", len(policy["missing_topics"]))
        for record in policy["topics"]:
            with st.expander(record["topic"]):
                st.markdown(f"**Summary:** {record['summary']}")
                st.markdown("**Original supporting excerpts:**")
                for excerpt in record["excerpts"]:
                    st.markdown(f"> {excerpt}")
        if policy["missing_topics"]:
            st.markdown("### Topics not mentioned or not determined")
            for topic in policy["missing_topics"]:
                st.markdown(f"- {topic}")

elif page == "Transparency comparison":
    render_header("Permission–policy transparency", "Compare declared requests with policy topics and identify review questions.")
    permission_analysis = st.session_state.get("permission_analysis")
    policy_analysis = st.session_state.get("policy_analysis")
    if not permission_analysis:
        st.info("Upload and analyze a manifest or APK first.")
    elif not policy_analysis:
        st.info("Analyze a privacy policy before comparing findings.")
    else:
        with st.spinner("Matching permissions to policy evidence…"):
            comparison = compare_permissions_with_policy(permission_analysis, policy_analysis)
        st.session_state["policy_comparison"] = comparison
        c1, c2, c3 = st.columns(3)
        c1.metric("Policy coverage found", comparison["coverage_count"])
        c2.metric("Potential transparency gaps", comparison["gap_count"])
        c3.metric("Unknown permissions", comparison["unknown_count"])
        if comparison["comparisons"]:
            rows = [{
                "Permission identifier": r["permission"],
                "Status": r["status"],
                "Relevant policy topic": r["relevant_policy_topic"] or "Not available",
                "Reason": r["reason"],
                "Supporting excerpts": " | ".join(r["supporting_excerpts"]),
            } for r in comparison["comparisons"]]
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
        if comparison["unknown_permissions"]:
            st.markdown("### Unknown permissions")
            st.dataframe(pd.DataFrame(comparison["unknown_permissions"]), use_container_width=True, hide_index=True)
        st.caption("Missing policy statements indicate potential transparency gaps, not proof of wrongdoing or actual data access.")

elif page == "Purpose review":
    render_header("Application purpose comparison", "Optional review questions based only on the supplied description and known permissions.")
    result = st.session_state.get("purpose_result")
    if not result:
        st.info("Provide an application name or purpose in Analysis inputs, then run the purpose review.")
    elif not result["performed"]:
        st.warning(result["message"])
    else:
        st.markdown(f'<div class="card"><h3>Review summary</h3><p>{result["message"]}</p></div>', unsafe_allow_html=True)
        rows = [{
            "Permission identifier": r["permission"],
            "Known capability": r["capability"],
            "Assessment": r["assessment"],
            "Explanation": r["explanation"],
        } for r in result["assessments"]]
        if rows:
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
        unknown_rows = [{
            "Permission identifier": r["permission"],
            "Assessment": r["assessment"],
            "Capability": r["capability"],
            "Explanation": r["explanation"],
        } for r in result["unknown_permissions"]]
        if unknown_rows:
            st.markdown("### Unknown permissions")
            st.dataframe(pd.DataFrame(unknown_rows), use_container_width=True, hide_index=True)
        if not rows and not unknown_rows:
            st.info("No recognized or unknown permission results were available for this assessment.")
        st.caption("Purpose review is a review aid. It does not establish actual behavior, safety, or malicious intent.")

elif page == "Reports":
    render_header("Analysis reports", "Generate evidence-linked outputs containing the actual completed results.")
    permission_analysis = st.session_state.get("permission_analysis")
    policy_analysis = st.session_state.get("policy_analysis")
    comparison = st.session_state.get("policy_comparison")
    if permission_analysis and policy_analysis and comparison is None:
        comparison = compare_permissions_with_policy(permission_analysis, policy_analysis)
        st.session_state["policy_comparison"] = comparison
    purpose_result = st.session_state.get("purpose_result")
    application_name = st.session_state.get("application_name", "")
    application_purpose = st.session_state.get("application_purpose", "")

    if not permission_analysis and not policy_analysis and not purpose_result:
        st.info("Complete at least one analysis before generating a report.")
    else:
        if st.button("Generate reports", type="primary"):
            with st.spinner("Preparing Markdown and JSON reports…"):
                report_markdown = generate_report_markdown(
                    permission_analysis=permission_analysis,
                    policy_analysis=policy_analysis,
                    policy_comparison=comparison,
                    purpose_result=purpose_result,
                    application_name=application_name,
                    application_purpose=application_purpose,
                )
                report_json = generate_report_json(
                    permission_analysis=permission_analysis,
                    policy_analysis=policy_analysis,
                    comparison=comparison,
                    purpose=purpose_result,
                    application_name=application_name,
                    application_purpose=application_purpose,
                )
            st.session_state["report_markdown"] = report_markdown
            st.session_state["report_json"] = report_json
            st.success("Reports generated successfully.")

        c1, c2 = st.columns(2)
        with c1:
            st.markdown('<div class="card"><h3>Markdown report</h3><p>Human-readable findings, evidence excerpts, comparisons, and limitations.</p></div>', unsafe_allow_html=True)
            if st.session_state.get("report_markdown"):
                st.download_button("Download Markdown (.md)", st.session_state["report_markdown"], "ps01_privacy_analysis_report.md", "text/markdown")
        with c2:
            st.markdown('<div class="card"><h3>JSON report</h3><p>Structured data for verification, records, and machine-readable review.</p></div>', unsafe_allow_html=True)
            if st.session_state.get("report_json"):
                st.download_button("Download JSON (.json)", st.session_state["report_json"], "ps01_privacy_analysis_report.json", "application/json")

st.caption("Privacy and Permission Analyzer · Evidence-led analysis · Declarations do not prove actual application behavior")
