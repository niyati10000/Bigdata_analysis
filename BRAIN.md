# BRAIN.md — read this first, every session

> Context anchor for any AI agent (Claude Code, Antigravity, etc.) or human picking up this project.
> Read this file fully before touching anything. Then read the file relevant to your task.

## One-line pitch

**VeriCite** — a fact-verification system that checks a claim against 5.4M Wikipedia pages and returns a verdict (Supported / Refuted / Not Enough Info) with an explanation and **citations to the exact sentences used**. Evaluated on FEVER, so every number is measured, not claimed.

## Why this exists

Resume project. 3-day build. Must show: big data (Spark), NLP (retrieval + LLM reasoning), and honest evaluation. Not a research breakthrough — RAG fact-checking on FEVER has been done before. The honest contribution is the **error breakdown**: when a verdict is wrong, was it retrieval's fault or the LLM's fault?

**Separate from the fetal-ultrasound capstone.** Do not mix files, folders, or context.

## Core flow

```
claim
  → dense retrieval (FAISS, page level)  ┐
  → BM25 retrieval (page level)          ┴→ hybrid merge (RRF) → top-k pages
  → sentence selection inside those pages → top-5 evidence sentences
  → LLM (claim + 5 sentences, JSON output) → verdict + explanation + cited sentence ids
  → citation check (drop any cited id not in the 5 given) → final answer
```

## Locked-in decisions (do not re-argue)

| Decision | Choice | Why |
|---|---|---|
| Dataset | FEVER (claims + gold evidence + 2017 Wikipedia dump) | Labels + gold evidence = real evaluation without manual annotation |
| Big data layer | PySpark, local mode, on Kaggle | 5.4M pages / ~25M sentences genuinely needs it |
| Retrieval unit | Page first, then sentence | Embedding all ~25M sentences won't fit in RAM or time |
| Embedding model | `sentence-transformers/all-MiniLM-L6-v2` (384-d) | Fast enough on a T4 for 5.4M passages |
| Vector index | FAISS `IndexIVFPQ` | Compresses ~8 GB of vectors to a few hundred MB, so it fits on a free host |
| Sparse retrieval | `bm25s` | Pure Python, handles millions of docs, no Java |
| Hybrid merge | Reciprocal Rank Fusion (k=60) | No tuning needed |
| LLM | Free API tier (Groq or Gemini), model name in config | No GPU needed for generation; swap models freely |
| Eval set | 1,000 claims sampled from FEVER `shared_task_dev`, fixed seed 42 | Enough for stable numbers, fits free-tier limits |
| Demo | Gradio on Hugging Face Spaces (free CPU) | Clickable link for recruiters |
| Code format | Notebook cells on Kaggle (numbered `K1_`, `K2_`…). Only exception: `app.py` for the HF Space | Owner's working style |
| No users / no login | Public demo, rate limited by IP | Nothing to protect per-user; less to build |
| Streaming ingestion, triage classifier | **Cut** | Add nothing in 3 days |

## Glossary

- **FEVER** — Fact Extraction and VERification dataset. ~145k train claims, ~20k labeled dev claims.
- **SUPPORTS / REFUTES / NOT ENOUGH INFO (NEI)** — the three FEVER labels.
- **Gold evidence** — the Wikipedia (page, sentence_id) pairs annotators said prove the label.
- **Page recall@k** — % of claims where at least one full gold evidence set's pages are in the top-k retrieved pages.
- **Evidence recall@5** — % of claims where a full gold evidence set is inside the 5 selected sentences.
- **Label accuracy** — % of claims with the correct verdict.
- **FEVER score** — correct verdict AND full gold evidence in top 5 (NEI needs label only). The strict metric.
- **Citation faithfulness** — % of LLM-cited sentence ids that were actually given to it. Invented ids = hallucination.
- **RRF** — Reciprocal Rank Fusion: score = Σ 1/(60 + rank).
- **Retrieval failure vs reasoning failure** — wrong verdict where gold evidence was missing (retrieval) vs present (reasoning).

## File map

| File | Read when |
|---|---|
| `BRAIN.md` | Always, first |
| `PLAN.md` | Deciding what to do next |
| `ARCHITECTURE.md` | Writing any code |
| `DATABASE_SCHEMA.md` | Reading/writing any data file |
| `DESIGN_SYSTEM.md` | Touching the Gradio UI or charts |
| `SECURITY_AND_ACCESS.md` | API keys, deployment, the public demo |
| `ANTIGRAVITY.md` | Running the build with an AI agent — has every prompt in order |

## Rules for any agent

1. One step at a time. Finish a cell, run it, confirm output, then next.
2. Never hardcode API keys. See `SECURITY_AND_ACCESS.md`.
3. Never change a locked-in decision without the owner saying so.
4. Every number in the README must come from an output file in `results/`. No invented metrics.
5. Update the status line below at the end of every session.

## Status

```
Phase: Complete (All 6 Phases Finished)
Last done: Public Demo live on Hugging Face Spaces: https://huggingface.co/spaces/Niyati26/vericite
All metrics produced and saved in results/:
- Dense Recall@20: 97.45%
- BM25 Recall@20: 96.70%
- Hybrid (RRF) Recall@20: 98.65%
- 1,000 FEVER Dev Claims Evaluated
- Error breakdown chart saved in results/figures/
Blockers: none
Updated: 2026-10-12
```
