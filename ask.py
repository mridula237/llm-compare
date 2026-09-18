import argparse
import time
import anthropic
from openai import OpenAI
import hashlib
import json
import sqlite3

CLAUDE_MODEL = "claude-haiku-4-5-20251001"
GPT_MODEL = "gpt-5.4-nano"
MAX_TOKENS = 1024

claude = anthropic.Anthropic()
gpt = OpenAI()

DB = sqlite3.connect("cache.db")
DB.execute("CREATE TABLE IF NOT EXISTS cache (key TEXT PRIMARY KEY, response TEXT)")


def cached(fn, model, prompt, system=None, stream=False):
    """Return a saved response if this exact model+system+prompt was asked before."""
    if stream: 
        return fn(prompt, system, stream)
    key = hashlib.sha256(json.dumps([model, system, prompt]).encode()).hexdigest()
    row = DB.execute("SELECT response FROM cache WHERE key = ?", (key,)).fetchone()
    if row:
        r = json.loads(row[0])
        r["cached"] = True
        return r
    r = fn(prompt, system, stream)
    DB.execute("INSERT OR REPLACE INTO cache VALUES (?, ?)", (key, json.dumps(r)))
    DB.commit()
    r["cached"] = False
    return r

def ask_claude(prompt, system=None, stream=False):
    kwargs = dict(model=CLAUDE_MODEL, max_tokens=MAX_TOKENS,
                  messages=[{"role": "user", "content": prompt}])
    if system:
        kwargs["system"] = system 

    start = time.perf_counter()
    ttft = None  
    if stream:
        print(f"\n===== {CLAUDE_MODEL} =====")
        with claude.messages.stream(**kwargs) as s:
            for piece in s.text_stream:
                if ttft is None:
                    ttft = time.perf_counter() - start
                print(piece, end="", flush=True)
            r = s.get_final_message()
        print()
    else:
        r = claude.messages.create(**kwargs)
    latency = time.perf_counter() - start

    text = "".join(b.text for b in r.content if b.type == "text")
    return {"model": CLAUDE_MODEL, "text": text,
            "in": r.usage.input_tokens, "out": r.usage.output_tokens,
            "latency": latency, "ttft": ttft}


def ask_gpt(prompt, system=None, stream=False):
    messages = []
    if system:
        messages.append({"role": "system", "content": system})  
    messages.append({"role": "user", "content": prompt})
    kwargs = dict(model=GPT_MODEL, max_completion_tokens=MAX_TOKENS, messages=messages)

    start = time.perf_counter()
    ttft = None
    if stream:
        print(f"\n===== {GPT_MODEL} =====")
        pieces, usage = [], None
        for chunk in gpt.chat.completions.create(
            **kwargs, stream=True, stream_options={"include_usage": True}
        ):
            if chunk.usage:  
                usage = chunk.usage
            if chunk.choices and chunk.choices[0].delta.content:
                if ttft is None:
                    ttft = time.perf_counter() - start
                piece = chunk.choices[0].delta.content
                pieces.append(piece)
                print(piece, end="", flush=True)
        print()
        text, in_tok, out_tok = "".join(pieces), usage.prompt_tokens, usage.completion_tokens
    else:
        r = gpt.chat.completions.create(**kwargs)
        text, in_tok, out_tok = r.choices[0].message.content, r.usage.prompt_tokens, r.usage.completion_tokens
    latency = time.perf_counter() - start

    return {"model": GPT_MODEL, "text": text, "in": in_tok, "out": out_tok,
            "latency": latency, "ttft": ttft}


def main():
    parser = argparse.ArgumentParser(description="Ask Claude and GPT the same prompt")
    parser.add_argument("prompt", help="The prompt to send")
    parser.add_argument("--stream", action="store_true", help="Print tokens as they arrive")
    parser.add_argument("--system", default=None, help='e.g. "You are a helpful expert in X"')
    args = parser.parse_args()

    results = [cached(ask_claude, CLAUDE_MODEL, args.prompt, args.system, args.stream),
               cached(ask_gpt, GPT_MODEL, args.prompt, args.system, args.stream)]
    if not args.stream and all(r["cached"] for r in results):
        print("(cached, no API calls made, $0)")

    if not args.stream: 
        for r in results:
            print(f"\n===== {r['model']} =====")
            print(r["text"])

    print("\n" + "-" * 70)
    print(f"{'Model':<30}{'In':>7}{'Out':>7}{'TTFT':>10}{'Latency':>12}")
    for r in results:
        ttft = f"{r['ttft']:.2f}s" if r["ttft"] else "-"
        print(f"{r['model']:<30}{r['in']:>7}{r['out']:>7}{ttft:>10}{r['latency']:>11.2f}s")


if __name__ == "__main__":
    main()