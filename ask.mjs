import Anthropic from "@anthropic-ai/sdk";
import OpenAI from "openai";
import { parseArgs } from "node:util";

const CLAUDE_MODEL = "claude-haiku-4-5-20251001";
const GPT_MODEL = "gpt-5.4-nano";
const MAX_TOKENS = 1024;

const claude = new Anthropic();
const gpt = new OpenAI();       

async function askClaude(prompt, system, stream) {
  const params = { model: CLAUDE_MODEL, max_tokens: MAX_TOKENS,
                   messages: [{ role: "user", content: prompt }] };
  if (system) params.system = system;

  const start = performance.now();
  let ttft = null, msg;
  if (stream) {
    console.log(`\n===== ${CLAUDE_MODEL} =====`);
    const s = claude.messages.stream(params);
    s.on("text", (piece) => {
      if (ttft === null) ttft = (performance.now() - start) / 1000;
      process.stdout.write(piece);
    });
    msg = await s.finalMessage();
    console.log();
  } else {
    msg = await claude.messages.create(params);
  }
  const latency = (performance.now() - start) / 1000;
  const text = msg.content.filter((b) => b.type === "text").map((b) => b.text).join("");
  return { model: CLAUDE_MODEL, text, in: msg.usage.input_tokens,
           out: msg.usage.output_tokens, latency, ttft };
}

async function askGpt(prompt, system, stream) {
  const messages = [];
  if (system) messages.push({ role: "system", content: system });
  messages.push({ role: "user", content: prompt });
  const params = { model: GPT_MODEL, max_completion_tokens: MAX_TOKENS, messages };

  const start = performance.now();
  let ttft = null, text, tokIn, tokOut;
  if (stream) {
    console.log(`\n===== ${GPT_MODEL} =====`);
    const s = await gpt.chat.completions.create({
      ...params, stream: true, stream_options: { include_usage: true },
    });
    const pieces = [];
    for await (const chunk of s) {
      if (chunk.usage) { tokIn = chunk.usage.prompt_tokens; tokOut = chunk.usage.completion_tokens; }
      const piece = chunk.choices?.[0]?.delta?.content;
      if (piece) {
        if (ttft === null) ttft = (performance.now() - start) / 1000;
        pieces.push(piece);
        process.stdout.write(piece);
      }
    }
    console.log();
    text = pieces.join("");
  } else {
    const r = await gpt.chat.completions.create(params);
    text = r.choices[0].message.content;
    tokIn = r.usage.prompt_tokens; tokOut = r.usage.completion_tokens;
  }
  const latency = (performance.now() - start) / 1000;
  return { model: GPT_MODEL, text, in: tokIn, out: tokOut, latency, ttft };
}


const { values, positionals } = parseArgs({
  allowPositionals: true,
  options: { stream: { type: "boolean", default: false }, system: { type: "string" } },
});
const prompt = positionals[0];
if (!prompt) {
  console.error('Usage: node ask.mjs "prompt" [--stream] [--system "..."]');
  process.exit(1);
}

const results = [
  await askClaude(prompt, values.system, values.stream),
  await askGpt(prompt, values.system, values.stream),
];

if (!values.stream) {
  for (const r of results) console.log(`\n===== ${r.model} =====\n${r.text}`);
}

console.log("\n" + "-".repeat(70));
console.log("Model".padEnd(30) + "In".padStart(7) + "Out".padStart(7) + "TTFT".padStart(10) + "Latency".padStart(12));
for (const r of results) {
  const ttft = r.ttft ? `${r.ttft.toFixed(2)}s` : "-";
  console.log(r.model.padEnd(30) + String(r.in).padStart(7) + String(r.out).padStart(7) +
              ttft.padStart(10) + `${r.latency.toFixed(2)}s`.padStart(12));
}