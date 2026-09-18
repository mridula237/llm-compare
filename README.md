# Claude vs GPT: 10-Prompt Comparison

**Models:** Claude Haiku 4.5 (`claude-haiku-4-5-20251001`) vs GPT-5.4 nano (`gpt-5.4-nano`), the cheapest current model from each provider.
**Method:** Same 10 prompts sent to both via `compare.py`; latency, tokens, and cost recorded in `results.json`.

## Head-to-head on 10 prompts

| # | Category | Prompt | Haiku 4.5 | GPT-5.4 nano | Better |
|---|---|---|---|---|---|
| 1 | Factual | Year Berlin Wall fell | 1989 | 1989 | Tie |
| 2 | Factual | Capital of Canada | Ottawa | Ottawa | Tie |
| 3 | Creative | 4-line poem, pipeline breaks at 3am | Loose rhyme, grammar slip, added a title | Clean rhyming couplets | nano |
| 4 | Creative | 3 robot coffee-shop names | Cleverer names (Brew.exe) + explanations | Plainer names | Haiku |
| 5 | Reasoning | Bat-and-ball puzzle | $0.05 (154 tokens) | $0.05 (99 tokens) | Tie |
| 6 | Reasoning | Syllogism | Yes | Yes | Tie |
| 7 | Coding | Python: 2nd largest unique | Correct, but ignored "code only" (docstring + tests, 321 tokens) | Correct, 2 lines (40 tokens) | nano |
| 8 | Coding | SQL: top 3 customers | Main query correct; extra "alternative" query is invalid (window function in `HAVING`) | Correct | nano |
| 9 | Classification | "Charged twice…" | billing | billing | Tie |
| 10 | Classification | "App crashes on upload" | technical | technical | Tie |

**Score:** 6 ties, nano better on 3, Haiku better on 1.

## Summary metrics

| Model | Avg latency | Output tokens | Total cost | Auto-checked correct |
|---|---|---|---|---|
| Claude Haiku 4.5 | 1.33s | 1010 | $0.0054 | 6/6 |
| GPT-5.4 nano | 1.14s | 343 | $0.0005 | 6/6 |

Prices per 1M tokens: Haiku $1.00 in / $5.00 out; nano $0.20 in / $1.25 out.

**Key difference:** accuracy was identical. The gap is verbosity and price. Haiku wrote ~3× more output, often adding content that wasn't asked for, which raises cost and, in #8, introduced an error.

## Recommendation: cheapest accurate model for customer-support classification

**Pick GPT-5.4 nano.**

1. **Equally accurate:** both returned the exact correct label on every classification ticket.
2. **~4.6× cheaper per ticket:** both used 4 output tokens per classification, so the difference is purely price per token:

   | | Per ticket | Per 100K tickets/month | Per 1M tickets |
   |---|---|---|---|
   | Haiku 4.5 | ~$0.0000705 | ~$7.05 | ~$70 |
   | GPT-5.4 nano | ~$0.0000154 | ~$1.54 | ~$15 |

3. **Stricter instruction-following:** nano stuck to the requested format (e.g., "code only"). A classifier's output feeds automated routing, so predictable, label-only output matters more than a clever explanation.
4. **Similar speed:** ~0.5–0.8s per classification for both, fine for real-time ticket routing.

**When I'd reconsider:** this test had only 2 classification tickets. Before committing, a startup should run 100+ real labeled tickets, including ambiguous multi-issue ones ("I can't log in and was charged twice"). If nano's accuracy drops meaningfully on those, Haiku's extra cost is small at startup volume and worth paying for accuracy.

## How to run
```bash
pip install anthropic openai
export ANTHROPIC_API_KEY=... OPENAI_API_KEY=...
python ask.py "Your prompt" [--stream] [--system "You are an expert in X"]
node ask.mjs "Your prompt" [--stream] [--system "You are an expert in X"]   
python compare.py   # runs all 10 prompts → results.json
```