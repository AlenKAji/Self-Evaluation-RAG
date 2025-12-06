import json
from statistics import mean

LOG_FILE = "history.jsonl"

def analyze_logs():
    entries = []
    with open(LOG_FILE, "r", encoding="utf-8") as f:
        for line in f:
            try:
                entries.append(json.loads(line))
            except json.JSONDecodeError:
                continue

    if not entries:
        print("No valid entries found.")
        return

    factual_scores = [e["evaluation"].get("factual_accuracy", 0) for e in entries]
    complete_scores = [e["evaluation"].get("completeness", 0) for e in entries]
    reasoning_scores = [e["evaluation"].get("reasoning_quality", 0) for e in entries]
    overall_scores = [e["evaluation"].get("overall", 0) for e in entries]

    print("📊 --- RAG Evaluation Summary ---")
    print(f"Total interactions: {len(entries)}")
    print(f"Average factual accuracy: {mean(factual_scores):.2f}")
    print(f"Average completeness: {mean(complete_scores):.2f}")
    print(f"Average reasoning quality: {mean(reasoning_scores):.2f}")
    print(f"Average overall score: {mean(overall_scores):.2f}")

    low_performance = [e for e in entries if e['evaluation'].get('overall', 0) < 6]
    if low_performance:
        print("\n⚠️ Low performing questions (<6 overall):")
        for e in low_performance:
            print(f" - {e['question']} ({e['evaluation'].get('overall', 0)})")

if __name__ == "__main__":
    analyze_logs()
