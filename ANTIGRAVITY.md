# ANTIGRAVITY.md — how to build this with an AI agent, and every prompt in order

Works for Antigravity, Claude Code, or any coding agent. Copy each prompt as-is. Run **one prompt at a time**. Don't send the next one until the current cell ran on Kaggle and you checked its output.

## How to use

1. Open the `vericite/` folder as the workspace so the agent can read all `.md` files.
2. Start **every** session with Prompt S0.
3. Agent writes a cell → you paste it into Kaggle → run → paste the output back to the agent.
4. If output looks wrong, use Prompt F1 (fix) before moving on.
5. End every session with Prompt S9.

## Agent rules (put in Antigravity's rules / workspace instructions)

```text
- Read BRAIN.md before doing anything. Follow its locked-in decisions.
- Output notebook cells only (one cell per response unless asked). No scripts, no argparse,
  no %%writefile, no !python, no imports between files. Exception: app.py for the HF Space.
- Name each cell with its id from ARCHITECTURE.md (e.g. "# K5_embed") as the first line.
- Reuse functions defined in earlier cells; don't redefine them.
- Never hardcode or print API keys. Use Kaggle Secrets / os.environ.
- Long jobs must be resumable (write shards/caches, skip what already exists).
- Every cell ends by printing a short, checkable summary (counts, sizes, times).
- Never invent metrics. Numbers only come from files in results/.
- Short, blunt explanations. One step at a time.
```

---

## Session prompts

**S0 — start of every session**
```text
Read BRAIN.md, then PLAN.md. Tell me in 3 lines: current phase, last completed step, and the single
next cell to write. Don't write code yet.
```

**S9 — end of every session**
```text
Update the Status block in BRAIN.md: phase, last done, next step, blockers, today's date.
Then list any numbers we produced today and which results/ file holds each one.
```

---

## Phase 0 — Setup

**P0.1**
```text
Write cell K0_setup per ARCHITECTURE.md: pip installs (pyspark, sentence-transformers, faiss-cpu,
bm25s, pyarrow), imports, a CONFIG dict (all paths, model names, seed=42, k values, FAISS params,
LLM model name), and create the output folders. Read the LLM key from Kaggle Secrets without
printing it — just print "key loaded: True/False".
```

**P0.2**
```text
Write a short check cell: count wiki-*.jsonl files (expect 109), print the first parsed line of
shared_task_dev.jsonl, and print the first wiki page's id and first two entries of its "lines" field.
```

## Phase 1 — Spark processing

**P1.1**
```text
Write K1_spark_session: local[*], driver memory 20g, shuffle partitions 64, Arrow enabled.
Print Spark version and UI-free confirmation.
```

**P1.2**
```text
Write K2_wiki_to_parquet per DATABASE_SCHEMA.md. Read all wiki jsonl with Spark. Write
pages.parquet (page_id, title, text, n_sentences) — title decodes -LRB-/-RRB-/-LSB-/-RSB-/-COLON-
and underscores. Explode "lines" into sentences.parquet (page_id, sent_id, text): each line is
"sent_id \t sentence \t anchor \t link ...", keep only the sentence. Drop empty pages and empty
sentences. Partition sentences by first char of page_id. Print counts and wall time.
```

**P1.3**
```text
Write K3_passages: build passages.parquet with row_idx (stable, 0..N-1, sorted by page_id),
page_id, passage = title + ". " + intro truncated to ~128 whitespace tokens. Print count and
3 sample rows.
```

**P1.4**
```text
Write K4_claims: parse train.jsonl and shared_task_dev.jsonl into claims.parquet and
evidence_gold.parquet per DATABASE_SCHEMA.md (evidence format is [[[ann_id, ev_id, page, sent_id]]],
group by inner list as evidence_set_id). Then sample eval_claims.parquet: 1,000 dev claims,
stratified by label, seed 42. If eval_claims.parquet already exists, do NOT overwrite it.
Print label counts.
```

## Phase 2 — Indexing

**P2.1**
```text
Write K5_embed: embed passages.parquet with all-MiniLM-L6-v2 on GPU, fp16, normalize, batch 512.
Save shards of 200k rows to emb/shard_XXXX.npy. Skip shards that already exist (resumable).
Show a progress bar, print rows/sec and total time.
```

**P2.2**
```text
Write K6_faiss: train IndexIVFPQ (inner product, nlist=16384, m=48, nbits=8) on a 500k random
sample of the embeddings (seed 42), add all shards in order so FAISS id == row_idx, set nprobe=32,
save faiss.index and faiss_id_map.parquet. Print index size on disk, train time, add time.
```

**P2.3**
```text
Write K7_bm25: build a bm25s index over passages (lowercase, English stopwords), doc order ==
row_idx, save to bm25/. Print build time and size on disk.
```

**P2.4**
```text
Write a sanity cell: query "Barack Obama", "The Eiffel Tower is in Paris", "Nikola Tesla invented
the radio" with both FAISS and BM25, print top 5 page titles each. Barack_Obama should be top 3.
```

## Phase 3 — Retrieval eval

**P3.1**
```text
Write K8_retrieval_fns with dense_search, bm25_search, rrf_merge, select_sentences exactly per the
contracts in ARCHITECTURE.md. select_sentences loads only the sentences of the given pages
(filter sentences.parquet by page_id), embeds them, ranks by cosine vs claim, returns top 5.
Include a tiny self-test at the bottom.
```

**P3.2**
```text
Write K9_retrieval_eval: for all 1,000 eval claims and each method (dense, bm25, hybrid) compute
top-20 pages and top-5 sentences, page_hit@5/10/20, evidence_hit@5 (a hit = at least one complete
gold evidence set covered; NEI claims excluded from recall). Save retrieval_results.parquet and
results/retrieval_metrics.csv. Print the metrics table. Resumable.
```

## Phase 4 — LLM verdicts

**P4.1**
```text
Write K10_llm_fns per the "LLM prompt contract" in ARCHITECTURE.md and the prompt-injection rules
in SECURITY_AND_ACCESS.md: build_prompt (with and without evidence), call_llm (temperature 0,
retries with exponential backoff on 429/5xx, disk cache in llm_cache/ keyed by sha256(prompt+model)),
parse_verdict (strict JSON, one retry, else NEI + parse_ok=False), check_citations.
Test on 3 claims and print the parsed results.
```

**P4.2**
```text
Write K11_run_verdicts: run all 1,000 eval claims in both conditions (with_evidence using hybrid
top-5 sentences, no_evidence). Respect rate limits (sleep between calls, configurable). Write
verdicts.parquet per DATABASE_SCHEMA.md. Resumable via cache. Print progress every 50 claims and
final parse-failure rate.
```

## Phase 5 — Analysis

**P5.1**
```text
Write K12_metrics: for each condition compute label accuracy, FEVER score, macro-F1, confusion
matrix, citation faithfulness (% cited ids that were valid), parse-fail rate. Save
results/eval_metrics.csv. Print a clean table.
```

**P5.2**
```text
Write K13_error_analysis: for wrong with_evidence verdicts on SUPPORTS/REFUTES claims, label each
as retrieval_failure (no complete gold set in top 5) or reasoning_failure (gold set present).
Break down by true label. Save results/error_breakdown.csv. Then pick 5 diverse failures and
write results/failure_examples.md with claim, gold label, verdict, evidence given, one-line reason.
```

**P5.3**
```text
Write K14_figures using the chart rules in DESIGN_SYSTEM.md: (1) recall@k per retrieval method,
(2) accuracy + FEVER score, with vs without evidence, (3) error breakdown stacked bar,
(4) confusion matrix for with_evidence. Save PNGs at 200 dpi to results/figures/.
```

## Phase 6 — Demo + README

**P6.1**
```text
Write K15_export_for_demo: copy faiss.index, faiss_id_map.parquet, passages page_id+title, and
sentences.parquet into demo_assets/, then upload demo_assets to a new HF dataset repo using
HF_TOKEN from Kaggle Secrets. Print total upload size.
```

**P6.2**
```text
Write app.py for a Hugging Face Space (the one non-notebook file). On startup download demo_assets
with snapshot_download, load model + FAISS (+ BM25 if it fits, else dense-only with a visible note).
Implement verify() per ARCHITECTURE.md and the UI per DESIGN_SYSTEM.md exactly (palette, fonts,
verdict card, evidence list with cited highlighting, status line, 4 example chips, footer
disclaimer). Add every control in SECURITY_AND_ACCESS.md: input limits, per-IP token bucket,
global daily cap, queue limits, 15 s LLM timeout, claim cache, no claim logging.
Also give me requirements.txt.
```

**P6.3**
```text
Go through the pre-launch checklist in SECURITY_AND_ACCESS.md one item at a time. For each,
tell me exactly how to test it on the live Space and what result to expect.
```

**P6.4**
```text
Write README.md: one-line pitch, demo link placeholder, architecture diagram (mermaid), dataset
and scale numbers, metrics tables and the 4 figures, error-breakdown finding in plain words,
honest limitations (2017 snapshot, 1,000-claim eval, free-tier LLM, not novel — RAG on FEVER is
known), how to reproduce. Every number must be read from results/ files — show me which file each
came from.
```

**P6.5**
```text
Write 3 resume bullets for this project, each with a real number from results/. Max 25 words each.
No buzzwords.
```

---

## Fix / helper prompts (use any time)

**F1 — cell failed or output looks wrong**
```text
Here is the cell and its full output/error: <paste>. Find the root cause. Give me the fixed cell
only, and one line on what was wrong. Don't change anything unrelated.
```

**F2 — out of memory / too slow**
```text
This cell ran out of memory / is too slow: <paste output>. Kaggle limits: ~30 GB RAM, T4 16 GB,
20 GB disk output. Rewrite it to fit, keeping results identical. Explain the change in one line.
```

**F3 — explain it so I can defend it in an interview**
```text
Explain cell <id> as if an interviewer is asking me about it: what it does, why this choice over
the obvious alternative, and one weakness. Under 150 words.
```

**F4 — sanity check the numbers**
```text
Look at results/eval_metrics.csv and results/retrieval_metrics.csv. Do these numbers look plausible
for FEVER with this setup? Flag anything suspicious (leakage, bugs, too-good-to-be-true).
```

**F5 — stretch goal (only after Phase 6 is done)**
```text
Add a cross-encoder re-ranker (cross-encoder/ms-marco-MiniLM-L-6-v2) to sentence selection as a
new cell after K8. Re-run evidence recall@5 for hybrid only and add a row "hybrid+rerank" to
retrieval_metrics.csv. Don't touch existing results.
```
