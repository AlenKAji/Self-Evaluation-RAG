# evaluator.py
import json
import re
from ollama import chat
from config import EVALUATION_MODEL

EVAL_SYSTEM_PROMPT = """
You are an evaluation assistant.
You will be given:
- a question
- the model's answer
- the retrieved context

You must respond ONLY with a JSON object with keys:
- factual_accuracy (0-10)
- completeness (0-10)
- reasoning_quality (0-10)
- overall (0-10)
- confidence (0.0-1.0)
- feedback (short natural language string)
"""

def evaluate_answer(question: str, answer: str, context: str):
    prompt = f"""{EVAL_SYSTEM_PROMPT}

Question: {question}
Context: {context}
Answer: {answer}
"""
    try:
        res = chat(
            model=EVALUATION_MODEL,
            messages=[{"role": "user", "content": prompt}]
        )
        content = res["message"]["content"]
    except Exception as e:
        return {
            "factual_accuracy": 0,
            "completeness": 0,
            "reasoning_quality": 0,
            "overall": 0,
            "confidence": 0.0,
            "feedback": f"Evaluation failed: {e}"
        }

    # Extract JSON from content
    try:
        # if it's already JSON
        if isinstance(content, dict):
            return content

        match = re.search(r"\{.*\}", content, re.DOTALL)
        if match:
            return json.loads(match.group())
    except Exception:
        pass

    # Fallback
    return {
        "factual_accuracy": 0,
        "completeness": 0,
        "reasoning_quality": 0,
        "overall": 0,
        "confidence": 0.0,
        "feedback": f"Evaluation text (unparsed): {content}"
    }
