import json
from datetime import datetime

from ask import ask_claude, ask_gpt, ask_oss, cached, CLAUDE_MODEL, GPT_MODEL, OSS_MODEL
PRICES = {
    CLAUDE_MODEL: (1.00, 5.00),
    GPT_MODEL: (0.20, 1.25),
    OSS_MODEL: (0.075, 0.30),
}

CLASSIFY_SYSTEM = (

    "You are a customer-support ticket classifier. Reply with exactly one label: "
    "billing, technical, shipping, account, or other. No other text."
)

# 'expected' = acceptable answers for a rough auto-check (creative/coding are judged manually)
PROMPTS = [
    {"id": 1, "category": "factual", "prompt": "What year did the Berlin Wall fall? Answer with just the year.", "expected": ["1989"]},
    {"id": 2, "category": "factual", "prompt": "What is the capital of Canada? One word.", "expected": ["ottawa"]},
    {"id": 3, "category": "creative", "prompt": "Write a 4-line poem about a data pipeline breaking at 3am."},
    {"id": 4, "category": "creative", "prompt": "Give 3 catchy names for a coffee shop run by robots."},
    {"id": 5, "category": "reasoning", "prompt": "A bat and a ball cost $1.10 total. The bat costs $1.00 more than the ball. How much is the ball? Brief reasoning, then the answer.", "expected": ["0.05", "5 cents", "five cents"]},
    {"id": 6, "category": "reasoning", "prompt": "All bloops are razzies and all razzies are lazzies. Are all bloops definitely lazzies? Answer yes or no, then one sentence why.", "expected": ["yes"]},
    {"id": 7, "category": "coding", "prompt": "Write a Python function that returns the second largest unique number in a list, or None if it doesn't exist. Code only."},
    {"id": 8, "category": "coding", "prompt": "Write a SQL query for the top 3 customers by total order amount, given customers(id, name) and orders(id, customer_id, amount)."},
    {"id": 9, "category": "classification", "system": CLASSIFY_SYSTEM, "prompt": "I was charged twice for my subscription this month, please refund one.", "expected": ["billing"]},
    {"id": 10, "category": "classification", "system": CLASSIFY_SYSTEM, "prompt": "The app crashes every time I try to upload a photo.", "expected": ["technical"]},
]


def cost(model, tokens_in, tokens_out):
    p_in, p_out = PRICES[model]
    return tokens_in / 1e6 * p_in + tokens_out / 1e6 * p_out


def run():
    results = []
    for p in PROMPTS:
        print(f"[{p['id']}/{len(PROMPTS)}] {p['category']}: {p['prompt'][:50]}...")
        for fn, model in ((ask_claude, CLAUDE_MODEL), (ask_gpt, GPT_MODEL), (ask_oss, OSS_MODEL)):
            try:
                r = cached(fn, model, p["prompt"], p.get("system"))
                r["cost"] = cost(model, r["in"], r["out"])
                r["error"] = None
            except Exception as e: 
                r = {"model": model, "text": "", "in": 0, "out": 0,
                     "latency": 0, "ttft": None, "cost": 0, "error": str(e)}
            if "expected" in p and not r["error"]:
                r["correct"] = any(e in r["text"].lower() for e in p["expected"])
            r.update(id=p["id"], category=p["category"], prompt=p["prompt"])
            results.append(r)
    return results


def summarize(results):
    summary = {}
    for model in PRICES:
        rows = [r for r in results if r["model"] == model and not r["error"]]
        checked = [r for r in rows if "correct" in r]
        summary[model] = {
            "ok_calls": len(rows),
            "avg_latency_s": round(sum(r["latency"] for r in rows) / max(len(rows), 1), 3),
            "total_in_tokens": sum(r["in"] for r in rows),
            "total_out_tokens": sum(r["out"] for r in rows),
            "total_cost_usd": round(sum(r["cost"] for r in rows), 6),
            "auto_checked_correct": f"{sum(r['correct'] for r in checked)}/{len(checked)}",
        }
    return summary


def main():
    results = run()
    summary = summarize(results)

    with open("results.json", "w") as f:
        json.dump({"run_at": datetime.now().isoformat(), "prices_per_1M": PRICES,
                   "summary": summary, "results": results}, f, indent=2)

    print("\n" + "-" * 90)
    print(f"{'Model':<28}{'Avg lat':>9}{'In tok':>9}{'Out tok':>9}{'Cost $':>12}{'Correct':>10}")
    for model, s in summary.items():
        print(f"{model:<28}{s['avg_latency_s']:>8.2f}s{s['total_in_tokens']:>9}"
              f"{s['total_out_tokens']:>9}{s['total_cost_usd']:>12.6f}{s['auto_checked_correct']:>10}")
    errors = [r for r in results if r["error"]]
    if errors:
        print(f"\n⚠️ {len(errors)} failed calls, see results.json")
    print("\nSaved to results.json")


if __name__ == "__main__":
    main()