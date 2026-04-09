# PromptForge ⚒️

**Local-first, model-aware prompt optimizer. No SaaS. No cloud. No shutdown.**

> PromptPerfect is shutting down September 1, 2026. Jina's prompt optimizer is gone. PromptForge fills that vacuum — open source, runs on your machine, works with every major model.

---

## What It Does

PromptForge takes a raw prompt and applies a pipeline of optimization passes:

| Pass | What it does |
|------|-------------|
| **Compress** | Strips filler words ("please can you", "I would like") — reduces token count |
| **Structure** | Adds context/task separation, formatting framing |
| **Techniques** | Chain-of-thought, role framing, output constraints, specificity |
| **Guardrails** | Anti-hallucination instructions, confidence calibration |
| **Model Adapt** | Claude → XML tags · GPT → Markdown · Llama → concise · Gemini → structured |

Results include **before/after diff**, **quality score (0–100)**, and **honest token stats** — if tokens go up because quality gains justify it, it says so.

---

## Install

```bash
pip install promptforge

# With Rich terminal UI + accurate token counting:
pip install promptforge[full]
```

---

## Usage

### Optimize a prompt
```bash
promptforge optimize "please can you tell me about neural networks"

promptforge optimize "explain this code" --model claude-3-5-sonnet

echo "summarize this document" | promptforge optimize --model gpt-4o
```

### Analyze quality without optimizing
```bash
promptforge analyze "write a blog post about AI"
```

### Benchmark across models
```bash
promptforge bench "explain transformer architecture" --models gpt-4o,claude-3-5-sonnet,llama-3-70b
```

### List supported models
```bash
promptforge models
```

---

## Example Output

```
──────────────── PromptForge — Optimize ────────────────

 BEFORE
 please can you tell me about machine learning

 AFTER
 You are an expert software engineer.

 tell me about machine learning

 Think step by step before giving your final answer.
 Use clear formatting with headers or bullets where appropriate.

 Metric          Before    After    Change
 Quality score      18       61      +43
   · Clarity         8       15       +7
   · Specificity     2       17      +15
   · Structure       4       17      +13
   · Grounding       4       12       +8
 Tokens             7        32   +25 (+357% — quality trade-off)

 Passes applied: compress, role_framing, chain_of_thought, output_constraints
```

---

## Why Local-First?

- **No API keys required** — optimization is structural, not generative
- **Privacy** — your prompts never leave your machine
- **No subscription that can shut down** — you own the tool
- **Extensible** — add your own passes in `techniques.py`

---

## Model Support

| Model | Family | Context | Style |
|-------|--------|---------|-------|
| claude-3-5-sonnet | Claude | 200K | XML tags |
| claude-3-opus | Claude | 200K | XML tags |
| gpt-4o | GPT | 128K | Markdown |
| gpt-3.5-turbo | GPT | 16K | Markdown (concise) |
| gemini-1.5-pro | Gemini | 1M | Markdown |
| llama-3-70b | Llama | 32K | Plain, concise |
| mistral-large | Mistral | 32K | Markdown |

---

## Architecture

```
promptforge/
├── cli.py          # CLI entry point (optimize, analyze, bench, models)
├── optimizer.py    # Orchestrates the pass pipeline
├── compress.py     # Token compression / filler removal
├── structure.py    # Prompt restructuring
├── techniques.py   # CoT, role framing, output constraints, specificity
├── guardrails.py   # Anti-hallucination, confidence calibration
├── model_adapt.py  # Model-specific formatting (Claude/GPT/Llama/Gemini)
├── scorer.py       # Quality scoring 0–100 (4 dimensions)
├── tokenizer.py    # Token counting (tiktoken + fallback)
└── models.py       # Model definitions and configs
```

---

## Part of the meda-claw AI Governance Ecosystem

PromptForge integrates with [meda-claw](https://github.com/VMaroon95/meda-claw) — a unified AI governance CLI. Use PromptForge to optimize prompts before they hit your agents; use meda-claw to audit what those agents do with them.

---

## License

MIT — use it, fork it, build on it.

---

*Built by [Varun Meda](https://vmaroon95.github.io) · Filling the vacuum left by PromptPerfect's shutdown (Sept 2026)*
