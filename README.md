# Claude vs GPT vs gpt-oss: 10-Prompt Comparison

**Models:** Claude Haiku 4.5 (`claude-haiku-4-5-20251001`), GPT-5.4 nano (`gpt-5.4-nano`), and gpt-oss-20b (`openai/gpt-oss-20b`, an open-weight model hosted on Groq).
**Method:** Same 10 prompts sent to all three via `compare.py`; latency, tokens, and cost recorded in `results.json`.

## Head-to-head on 10 prompts

| # | Category | Prompt | Haiku 4.5 | GPT-5.4 nano | gpt-oss-20b | Better |
|---|---|---|---|---|---|---|
| 1 | Factual | Year Berlin Wall fell | 1989 | 1989 | 1989 | Tie |
| 2 | Factual | Capital of Canada | Ottawa | Ottawa | Ottawa | Tie |
| 3 | Creative | 4-line poem, pipeline breaks at 3am | Rhymes (ABAB), added a title | Rhymes (AABB), vivid | Free verse, no rhyme | Haiku / nano |
| 4 | Creative | 3 robot coffee-shop names | Cleverest (Brew.exe) + explanations | Plain list | Solid names + taglines | Haiku |
| 5 | Reasoning | Bat-and-ball puzzle | $0.05 | $0.05 | $0.05 | Tie |
| 6 | Reasoning | Syllogism | Yes | Yes | Yes, but typo ("bleep") in explanation | Haiku / nano |
| 7 | Coding | Python: 2nd largest unique | **Unusable**: calls the Claude API to solve it | Correct, 5 lines | Correct, 3 lines + type hints | nano / gpt-oss |
| 8 | Coding | SQL: top 3 customers | Correct, but its "alternative with RANK" is a copy of the main query | Correct, concise | Correct + tie-handling version (verbose) | nano / gpt-oss |
| 9 | Classification | "Charged twice…" | billing | billing | billing | Tie |
| 10 | Classification | "App crashes on upload" | technical | technical | technical | Tie |

## Summary metrics

| Model | Avg latency | Input tok | Output tok | Total cost | Auto-checked correct |
|---|---|---|---|---|---|
| Claude Haiku 4.5 | 1.26s | 348 | 1145 | $0.0061 | 6/6 |
| GPT-5.4 nano | 1.14s | 333 | 334 | **$0.0005** | 6/6 |
| gpt-oss-20b (Groq) | **0.45s** | 981 | 2223 | $0.0007 | 6/6 |

Prices per 1M tokens (input / output): Haiku $1.00 / $5.00; nano $0.20 / $1.25; gpt-oss-20b $0.075 / $0.30.

**Key findings**
- **Accuracy was identical** on every auto-checkable prompt. The differences are cost, speed, and instruction-following.
- **Haiku is the most verbose and least reliable on code.** It wrote 3× nano's output and produced an unusable Python solution.
- **gpt-oss is the fastest** (~0.45s avg, thanks to Groq's hardware) but **token-hungry**: as a reasoning model, it spends hidden "thinking" tokens even on one-word answers, and Groq adds a system prompt to every call. Its low per-token price doesn't make it the cheapest.

## Recommendation: cheapest accurate model for customer-support classification

**Pick GPT-5.4 nano.**

| Model | Tokens per ticket (in / out) | Cost per ticket | Per 1M tickets | Latency |
|---|---|---|---|---|
| Claude Haiku 4.5 | ~50 / 4 | ~$0.0000705 | ~$70 | ~0.47s |
| **GPT-5.4 nano** | ~52 / 4 | **~$0.0000154** | **~$15** | ~0.77s |
| gpt-oss-20b | ~116 / ~55 | ~$0.0000252 | ~$25 | ~0.26s |

1. **Equally accurate:** all three labeled every ticket correctly.
2. **Cheapest in practice:** nano outputs just the label (4 tokens). gpt-oss's per-token price is lower, but its reasoning overhead makes it ~1.6× more expensive per ticket. Haiku is ~4.6× more expensive.
3. **Most predictable output:** nano followed format instructions most strictly across all 10 prompts, which matters when the label feeds an automated routing system.

**When I'd pick differently:**
- **Latency-critical routing:** gpt-oss on Groq was ~3× faster per ticket. Lowering its reasoning effort may also cut its token overhead enough to beat nano on cost, which is worth testing.
- **Data privacy:** gpt-oss is open-weight, so a startup could self-host it and keep customer tickets on its own servers.

**Caveat:** only 2 classification tickets were tested. Before production, run 100+ real labeled tickets, including ambiguous multi-issue ones ("I can't log in and was charged twice"), and compare per-label accuracy.

## Limitations
- Small sample, single run. Answers vary between runs: in an earlier run, Haiku's SQL "alternative" was invalid (window function in `HAVING`) rather than duplicated.
- Correctness auto-check is substring matching. Creative and coding answers were judged manually.
- Prices are hardcoded in `compare.py`; verify against official pricing pages.

## How to run
```bash
pip install anthropic openai
export ANTHROPIC_API_KEY=... OPENAI_API_KEY=... GROQ_API_KEY=...
python ask.py "Your prompt" [--stream] [--system "You are an expert in X"]
python compare.py            # runs all 10 prompts on 3 models → results.json
node ask.mjs "Your prompt" [--stream] [--system "..."]   # Node.js version (Claude + GPT)
```
Responses are cached in SQLite (`cache.db`), so re-running the same prompt costs $0.