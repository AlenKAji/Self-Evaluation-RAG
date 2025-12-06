# generator.py
from typing import List, Tuple
from ollama import chat

from config import GENERATION_MODEL, DEFAULT_WORKSPACE
from retriever import HybridRetriever
from evaluator import evaluate_answer

_retrievers = {}  # workspace_id -> HybridRetriever


def get_retriever(workspace_id: str = DEFAULT_WORKSPACE) -> HybridRetriever:
    global _retrievers
    if workspace_id not in _retrievers:
        _retrievers[workspace_id] = HybridRetriever(workspace_id=workspace_id)
    return _retrievers[workspace_id]


def generate_answer(question: str, workspace_id: str = DEFAULT_WORKSPACE) -> Tuple[str, List[str], List[str]]:
    retriever = get_retriever(workspace_id)
    contexts = retriever.search(question, top_k=5)
    context_text = "\n\n".join(contexts)

    prompt = f"""
You are a helpful assistant. Use ONLY the provided context to answer.

Context:
{context_text}

Question: {question}

Answer clearly and factually. If the answer is not in the context, say you don't know.
"""
    try:
        res = chat(
            model=GENERATION_MODEL,
            messages=[{"role": "user", "content": prompt}]
        )
        answer = res["message"]["content"].strip()
    except Exception as e:
        answer = f"Answer generation failed: {e}"

    return answer, contexts, contexts


def generate_self_correcting_answer(question: str, workspace_id: str = DEFAULT_WORKSPACE, max_attempts: int = 3):
    last_answer = None
    last_sources = None
    last_eval = None

    for attempt in range(1, max_attempts + 1):
        print(f"[GEN] Workspace={workspace_id} Attempt={attempt}")
        answer, sources, ctxs = generate_answer(question, workspace_id)
        evaluation = evaluate_answer(question, answer, "\n".join(ctxs))

        last_answer, last_sources, last_eval = answer, sources, evaluation

        # acceptance rule
        try:
            if evaluation.get("factual_accuracy", 0) >= 7 and evaluation.get("completeness", 0) >= 7:
                break
        except Exception:
            break  # if eval is not a dict, just return last

    return last_answer, last_sources, last_eval
