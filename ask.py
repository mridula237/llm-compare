import argparse
import time

import anthropic
from openai import OpenAI

CLAUDE_MODEL = "claude-haiku-4-5-20251001"
GPT_MODEL = "gpt-5.4-mini"
MAX_TOKENS = 1024

claude = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY
gpt = OpenAI()                  # reads OPENAI_API_KEY


def ask_claude(prompt):
    start = time.perf_counter()
    r = claude.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=MAX_TOKENS,
        messages=[{"role": "user", "content": prompt}],
    )
    latency = time.perf_counter() - start
    text = "".join(b.text for b in r.content if b.type == "text")
    return {"model": CLAUDE_MODEL, "text": text,
            "in": r.usage.input_tokens, "out": r.usage.output_tokens,
            "latency": latency}


def ask_gpt(prompt):
    start = time.perf_counter()
    r = gpt.chat.completions.create(
        model=GPT_MODEL,
        max_completion_tokens=MAX_TOKENS,
        messages=[{"role": "user", "content": prompt}],
    )
    latency = time.perf_counter() - start
    return {"model": GPT_MODEL, "text": r.choices[0].message.content,
            "in": r.usage.prompt_tokens, "out": r.usage.completion_tokens,
            "latency": latency}


def main():
    parser = argparse.ArgumentParser(description="Ask Claude and GPT the same prompt")
    parser.add_argument("prompt", help="The prompt to send")
    args = parser.parse_args()

    results = [ask_claude(args.prompt), ask_gpt(args.prompt)]

    for r in results:
        print(f"\n===== {r['model']} =====")
        print(r["text"])

    print("\n" + "-" * 60)
    print(f"{'Model':<30}{'In':>7}{'Out':>7}{'Latency':>12}")
    for r in results:
        print(f"{r['model']:<30}{r['in']:>7}{r['out']:>7}{r['latency']:>11.2f}s")


if __name__ == "__main__":
    main()