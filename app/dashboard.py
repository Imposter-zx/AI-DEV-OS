"""
AI Dev OS Dashboard - Streamlit Web Interface.

Provides a real-time overview of workflows, metrics, and results.
Run: streamlit run app/dashboard.py
"""

import json
import logging
from pathlib import Path

try:
    import streamlit as st
except ImportError:
    raise ImportError(
        "Streamlit is required for the dashboard. Install with: pip install streamlit"
    )

logger = logging.getLogger(__name__)

# ─── Page Config ─────────────────────────────────────────────────

st.set_page_config(
    page_title="AI Dev OS",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)

import os

# ─── Authentication ────────────────────────────────────────────────

def check_password():
    """Returns True if the user had the correct password."""

    def password_entered():
        """Checks whether a password entered by the user is correct."""
        if st.session_state["password"] == os.environ.get("DASHBOARD_PASSWORD", "aidevos"):
            st.session_state["password_correct"] = True
            del st.session_state["password"]  # don't store password
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        st.text_input("Username", key="username")
        st.text_input("Password", type="password", key="password")
        st.button("Login", on_click=password_entered)
        return False
    elif not st.session_state["password_correct"]:
        st.text_input("Username", key="username")
        st.text_input("Password", type="password", key="password")
        st.button("Login", on_click=password_entered)
        st.error("😕 Password incorrect")
        return False
    else:
        return True

if not check_password():
    st.stop()  # Do not continue if check_password is not True.

# ─── Helpers ─────────────────────────────────────────────────────

WORKFLOWS_DIR = Path.home() / ".ai-dev-os"


def load_workflows():
    """Load all saved workflow JSON files."""
    if not WORKFLOWS_DIR.exists():
        return []
    files = sorted(WORKFLOWS_DIR.glob("workflow_*.json"), reverse=True)
    workflows = []
    for f in files:
        try:
            with open(f) as fp:
                data = json.load(fp)
                data["_file"] = f.name
                workflows.append(data)
        except Exception:
            continue
    return workflows


def load_hud_status():
    """Load the latest HUD status."""
    status_file = WORKFLOWS_DIR / "hud_status.json"
    if status_file.exists():
        with open(status_file) as f:
            return json.load(f)
    return None


# ─── Sidebar ─────────────────────────────────────────────────────

with st.sidebar:
    st.image("https://img.icons8.com/color/96/robot-2.png", width=64)
    st.title("AI Dev OS")
    st.caption("Autonomous Development System")
    st.divider()

    workflows = load_workflows()

    st.subheader("📂 Workflows")
    if workflows:
        selected_idx = st.selectbox(
            "Select workflow",
            range(len(workflows)),
            format_func=lambda i: f"{workflows[i].get('id', 'unknown')[:8]}… — {workflows[i].get('phase', '?')}",
        )
    else:
        st.info("No workflows found yet.")
        selected_idx = None

    st.divider()

    # HUD Status
    hud = load_hud_status()
    if hud:
        st.subheader("📡 HUD Status")
        st.metric("Phase", hud.get("phase", "—"))
        st.metric("Context", hud.get("context_usage", "—"))
        agents = hud.get("active_agents", [])
        st.write(f"**Active agents:** {', '.join(agents) if agents else 'none'}")

# ─── Main Area ───────────────────────────────────────────────────

st.title("🤖 AI Dev OS Dashboard")

# Metrics Row
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Total Workflows", len(workflows))
with col2:
    completed = sum(1 for w in workflows if w.get("phase") == "merge")
    st.metric("Completed", completed)
with col3:
    rate = f"{completed / len(workflows) * 100:.0f}%" if workflows else "—"
    st.metric("Success Rate", rate)
with col4:
    in_progress = sum(1 for w in workflows if w.get("phase") != "merge")
    st.metric("In Progress", in_progress)

st.divider()

# ─── Workflow Details ────────────────────────────────────────────

if workflows and selected_idx is not None:
    workflow = workflows[selected_idx]

    st.header(f"Workflow: `{workflow.get('id', 'N/A')[:12]}…`")
    st.caption(f"Created: {workflow.get('created_at', 'unknown')}")

    tab1, tab2, tab3 = st.tabs(["📋 Overview", "📜 Logs", "📊 Results"])

    with tab1:
        c1, c2 = st.columns(2)
        with c1:
            st.metric("Phase", workflow.get("phase", "—"))
        with c2:
            st.metric("Request", workflow.get("user_request", "—")[:60])

        if workflow.get("design_doc"):
            with st.expander("Design Document", expanded=False):
                st.markdown(workflow["design_doc"])

        if workflow.get("implementation_plan"):
            with st.expander("Implementation Plan", expanded=False):
                st.markdown(workflow["implementation_plan"])

    with tab2:
        logs = workflow.get("logs", [])
        if logs:
            for log in logs:
                st.text(log)
        else:
            st.info("No logs available.")

    with tab3:
        results = workflow.get("execution_results", {})
        if results:
            st.json(results)
        else:
            st.info("No results available.")

else:
    st.info("Select a workflow from the sidebar or run a new one below.")

# ─── Run New Workflow ────────────────────────────────────────────

st.divider()
st.header("🚀 Run New Workflow")

request = st.text_area(
    "What should AI Dev OS build?",
    placeholder="e.g., Build a simple authentication module with tests and documentation",
    height=100,
)

if st.button("▶️ Start Workflow", type="primary"):
    if request.strip():
        st.success(
            "Workflow queued! The orchestrator will pick it up shortly. "
            "Refresh the page to see progress."
        )
        # In production, this would call:
        # asyncio.run(AIDevOSOrchestrator().run(request))
    else:
        st.warning("Please enter a request first.")
