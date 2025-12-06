import sys
import os
import subprocess
import json
from datetime import datetime

import streamlit as st
import pandas as pd

from generator import generate_self_correcting_answer
from config import (
    DEFAULT_WORKSPACE,
    get_workspace_paths,
)


# ==============================
# Smart Environment Check
# ==============================
EXPECTED_ENV = "ragenv312"
PYTHON_PATH = sys.executable.lower()
CURRENT_DIR = os.getcwd()

if EXPECTED_ENV.lower() not in PYTHON_PATH:
    st.error(
        f"🚨 You are not running inside the expected virtual environment: `{EXPECTED_ENV}`\n\n"
        f"Current Python interpreter:\n`{sys.executable}`"
    )

    st.warning("Please activate the correct environment to avoid FAISS/torch/numpy errors.")

    if st.button("⚙️ Auto-Activate Correct Environment and Restart"):
        activate_cmd = f'{EXPECTED_ENV}\\Scripts\\activate && streamlit run app.py'
        st.write("🔄 Restarting Streamlit in the correct environment...")
        try:
            subprocess.Popen(["cmd", "/c", activate_cmd], cwd=CURRENT_DIR)
            st.success("✅ Restart command executed. Please close this window if it doesn't auto-close.")
        except Exception as e:
            st.error(f"❌ Failed to run auto-fix: {e}")
        st.stop()

    st.stop()
else:
    st.success(f"✅ Running inside the correct environment:\n`{sys.executable}`")


# ==============================
# Streamlit Config
# ==============================
st.set_page_config(
    page_title="RAG Self-Evaluating Q&A",
    page_icon="🧠",
    layout="wide"
)

st.title("🧠 Retrieval-Augmented Generation with Self-Evaluation")
st.markdown("Ask questions and get answers grounded in your uploaded documents with built-in evaluation and feedback.")


# ==============================
# Workspace Selector (Sidebar)
# ==============================
st.sidebar.markdown("### 🗂 Workspace")

if "workspace_id" not in st.session_state:
    st.session_state["workspace_id"] = DEFAULT_WORKSPACE

workspace_input = st.sidebar.text_input("Workspace ID", value=st.session_state["workspace_id"])
workspace_id = workspace_input.strip() or DEFAULT_WORKSPACE
st.session_state["workspace_id"] = workspace_id

st.sidebar.markdown(f"**Active workspace:** `{workspace_id}`")

# Resolve workspace-specific paths
data_dir, index_dir, faiss_index_path, meta_path, log_dir = get_workspace_paths(workspace_id)


# ==============================
# Admin Login (Sidebar)
# ==============================
st.sidebar.title("🔐 Admin Access")

if "admin_logged_in" not in st.session_state:
    st.session_state["admin_logged_in"] = False

password = st.sidebar.text_input("Enter admin password:", type="password")
if st.sidebar.button("Login"):
    if password == "1234":
        st.session_state["admin_logged_in"] = True
        st.sidebar.success("✅ Logged in as Admin")
    else:
        st.sidebar.error("❌ Incorrect password")

if st.session_state["admin_logged_in"]:
    st.sidebar.success("🧠 Administrator Mode Active")


# ==============================
# Tabs
# ==============================
tab1, tab2, tab3 = st.tabs([
    "📄 Upload PDFs / Build Index",
    "💬 Ask Questions",
    "📊 Admin Dashboard"
])


# ==============================
# Tab 1: Upload PDFs + Rebuild Index
# ==============================
with tab1:
    st.subheader(f"Upload PDFs for workspace: `{workspace_id}`")
    uploaded_files = st.file_uploader(
        "Choose one or more PDF files",
        type=["pdf"],
        accept_multiple_files=True
    )

    if uploaded_files:
        saved_files = []
        for pdf in uploaded_files:
            save_path = os.path.join(data_dir, pdf.name)
            with open(save_path, "wb") as f:
                f.write(pdf.getbuffer())
            saved_files.append(pdf.name)

        st.success(f"✅ Uploaded {len(saved_files)} file(s) to workspace `{workspace_id}`: {', '.join(saved_files)}")

    st.markdown("### 🔄 Rebuild Index for this Workspace")
    if st.button("Rebuild FAISS Index"):
        with st.spinner(f"Rebuilding FAISS index for workspace `{workspace_id}`..."):
            try:
                result = subprocess.run(
                    [sys.executable, "build_index.py", "--workspace", workspace_id],
                    capture_output=True,
                    text=True,
                    check=True
                )
                st.success("✅ Index rebuilt successfully!")
                st.text_area("Build Log:", result.stdout or "(no stdout)", height=200)
            except subprocess.CalledProcessError as e:
                st.error("❌ Error rebuilding index.")
                st.code(e.stderr or str(e), language="bash")

    st.markdown("### 🧹 Clear Index for this Workspace")
    if st.button("Clear Index Files for Workspace"):
        removed = []
        for path in [faiss_index_path, meta_path]:
            if os.path.exists(path):
                os.remove(path)
                removed.append(path)
        if removed:
            st.success("🧹 Removed:\n" + "\n".join(f"- {p}" for p in removed))
        else:
            st.info("ℹ️ No index or metadata files found to remove.")


# ==============================
# Tab 2: Q&A with Self-Evaluation
# ==============================
with tab2:
    st.subheader(f"Ask a question about documents in workspace: `{workspace_id}`")

    if "answer_data" not in st.session_state:
        st.session_state["answer_data"] = None

    question = st.text_input("💬 Enter your question:")

    if st.button("Generate Answer"):
        if not question.strip():
            st.warning("Please enter a question first.")
        else:
            if not (os.path.exists(faiss_index_path) and os.path.exists(meta_path)):
                st.error(
                    f"❌ No FAISS index found for workspace `{workspace_id}`.\n\n"
                    "Go to **📄 Upload PDFs / Build Index** tab to upload PDFs and rebuild the index."
                )
            else:
                with st.spinner("Retrieving, generating, and evaluating..."):
                    try:
                        answer, sources, evaluation = generate_self_correcting_answer(
                            question,
                            workspace_id=workspace_id
                        )
                    except Exception as e:
                        st.error(f"❌ Error during generation/evaluation: {e}")
                        st.stop()

                st.session_state["answer_data"] = {
                    "workspace_id": workspace_id,
                    "question": question,
                    "answer": answer,
                    "sources": sources,
                    "evaluation": evaluation,
                }

    data = st.session_state.get("answer_data")
    if data and data.get("workspace_id") == workspace_id:
        st.markdown("### ✅ **Final Answer**")
        st.success(data["answer"])

        st.markdown("### 📚 **Top Sources Used**")
        sources = data.get("sources") or []
        if not sources:
            st.info("No sources returned (retrieval may have failed or index is empty).")
        else:
            for src in sources:
                st.write(f"- {src[:150].replace(os.linesep, ' ')}...")

        st.markdown("### 📊 **Self-Evaluation Report**")
        eval_obj = data.get("evaluation") or {}

        if isinstance(eval_obj, dict):
            col1, col2, col3, col4, col5 = st.columns(5)
            col1.metric("Factual", eval_obj.get("factual_accuracy", 0))
            col2.metric("Complete", eval_obj.get("completeness", 0))
            col3.metric("Reasoning", eval_obj.get("reasoning_quality", 0))
            col4.metric("Overall", round(eval_obj.get("overall", 0), 2))
            col5.metric("Conf.", round(eval_obj.get("confidence", 0.0), 2))

            st.code(json.dumps(eval_obj, indent=2, ensure_ascii=False), language="json")
        else:
            st.code(str(eval_obj), language="json")

        # Feedback section (workspace-specific log)
        st.markdown("---")
        st.markdown("### 💬 Was this answer helpful?")

        log_file = os.path.join(log_dir, "feedback_log.jsonl")

        def log_feedback(label: str):
            log_entry = {
                "timestamp": datetime.now().isoformat(),
                "workspace_id": workspace_id,
                "question": data["question"],
                "answer": data["answer"],
                "evaluation": eval_obj,
                "feedback": label,
            }
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
            st.success(f"✅ Feedback recorded: {label.capitalize()}")

        col1, col2 = st.columns(2)
        if col1.button("👍 Yes"):
            log_feedback("positive")
        if col2.button("👎 No"):
            log_feedback("negative")


# ==============================
# Tab 3: Admin Dashboard
# ==============================
with tab3:
    if not st.session_state["admin_logged_in"]:
        st.warning("🔒 Please log in as admin from the sidebar to access this section.")
    else:
        st.subheader(f"📈 Feedback & Evaluation Dashboard for workspace: `{workspace_id}`")

        log_file = os.path.join(log_dir, "feedback_log.jsonl")

        if not os.path.exists(log_file):
            st.info("No feedback yet for this workspace. Encourage users to ask questions and rate answers!")
        else:
            try:
                df = pd.read_json(log_file, lines=True)
            except ValueError:
                st.error("❌ Failed to read feedback log. File may be corrupted.")
                df = pd.DataFrame()

            if df.empty:
                st.info("Feedback log is empty.")
            else:
                st.markdown("### 🧾 Raw Feedback Log")
                st.dataframe(df, width="stretch")

                pos = df[df["feedback"] == "positive"].shape[0]
                neg = df[df["feedback"] == "negative"].shape[0]
                total = len(df)

                col1, col2, col3 = st.columns(3)
                col1.metric("👍 Positive", pos)
                col2.metric("👎 Negative", neg)
                col3.metric("📊 Total Feedback", total)

                def to_eval_dict(x):
                    if isinstance(x, dict):
                        return x
                    try:
                        return json.loads(x)
                    except Exception:
                        return {}

                eval_series = df["evaluation"].apply(to_eval_dict)
                eval_list = [e for e in eval_series if isinstance(e, dict) and e]

                if eval_list:
                    avg_accuracy = sum(e.get("factual_accuracy", 0) for e in eval_list) / len(eval_list)
                    avg_completeness = sum(e.get("completeness", 0) for e in eval_list) / len(eval_list)
                    avg_overall = sum(e.get("overall", 0) for e in eval_list) / len(eval_list)
                    avg_conf = sum(e.get("confidence", 0.0) for e in eval_list) / len(eval_list)

                    st.markdown("### 🧮 Average Evaluation Scores")
                    c1, c2, c3, c4 = st.columns(4)
                    c1.metric("Factual Accuracy", round(avg_accuracy, 2))
                    c2.metric("Completeness", round(avg_completeness, 2))
                    c3.metric("Overall", round(avg_overall, 2))
                    c4.metric("Confidence", round(avg_conf, 2))
                else:
                    st.info("ℹ️ Could not parse evaluation objects for averaging.")
