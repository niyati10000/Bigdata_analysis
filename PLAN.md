# PLAN.md — phased roadmap

Every phase ends with something you can show. Don't start a phase until the previous one's exit criteria pass.
Target: 3 days. Day mapping is a guide, not a promise.

---

## Phase 0 — Setup (Day 1, ~1 h)

**Do**
- Kaggle notebook, GPU T4 enabled, internet on.
- Add FEVER as input: `train.jsonl`, `shared_task_dev.jsonl`, `wiki-pages/` (109 `wiki-*.jsonl` files).
- Add `GROQ_API_KEY` (or `GEMINI_API_KEY`) to Kaggle Secrets.
- Install: `pyspark`, `sentence-transformers`, `faiss-cpu` (or `faiss-gpu`), `bm25s`, `pyarrow`.

**Exit criteria**
- Cell prints: number of wiki files = 109, first line of `shared_task_dev.jsonl` parsed.
- Secret reads without printing its value.

---

## Phase 1 — Spark processing (Day 1, ~3 h)

**Do**
- Spark session, local mode, all cores.
- Read all wiki pages → `pages.parquet` (drop empty pages, decode `-LRB-`/`-RRB-` etc. for display only, keep raw id as key).
- Explode the `lines` field → `sentences.parquet` (page_id, sent_id, text).
- Build page passages: title + first ~128 tokens of intro → `passages.parquet`.
- Parse claims + gold evidence → `claims.parquet`, `evidence_gold.parquet`.
- Sample 1,000 dev claims with seed 42 → `eval_claims.parquet`. Stratified by label.

**Exit criteria**
- Printed counts: ~5.4M pages, ~25M sentences, 1,000 eval claims (~333 per label).
- Printed Spark job time (goes in README).

---

## Phase 2 — Indexing (Day 1 evening → Day 2 morning, ~3 h, mostly waiting)

**Do**
- Embed all passages with MiniLM, fp16, batch 512, write shards to disk (resume-safe).
- Train FAISS `IndexIVFPQ` on a 500k sample, add all vectors, save index + id map.
- Build `bm25s` index over passages, save.
- Measure: index size on disk, query latency (median of 200 queries).

**Exit criteria**
- `faiss.index` + `faiss_id_map.parquet` + `bm25/` saved.
- Sanity check: query "Barack Obama" returns the Barack_Obama page in top 3.

---

## Phase 3 — Retrieval eval (Day 2, ~2 h)

**Do**
- For each of the 1,000 eval claims: dense top-20 pages, BM25 top-20, hybrid (RRF) top-20.
- Sentence selection: embed sentences of top-k pages on the fly, cosine vs claim, keep top 5.
- Compute page recall@{5,10,20} and evidence recall@5 for dense / BM25 / hybrid.

**Exit criteria**
- `results/retrieval_metrics.csv` with 3 rows (dense, bm25, hybrid).
- One chart: recall@k per method.

---

## Phase 4 — LLM verdicts (Day 2, ~3 h incl. rate-limit waiting)

**Do**
- Prompt: claim + 5 numbered sentences → strict JSON `{verdict, explanation, cited_ids}`.
- Run on 1,000 claims using hybrid retrieval. Cache every response to disk (resume-safe).
- Baseline: same LLM, **no evidence** (claim only).
- Citation check: drop cited ids not in the given 5; log how often that happens.

**Exit criteria**
- `verdicts.parquet` with 1,000 rows × 2 conditions (with evidence, no evidence).
- JSON parse failure rate printed (target < 2%).

---

## Phase 5 — Analysis (Day 3 morning, ~2 h)

**Do**
- Label accuracy, FEVER score, macro-F1, confusion matrix — for both conditions.
- Error breakdown on wrong verdicts: retrieval failure (gold missing) vs reasoning failure (gold present).
- Citation faithfulness %.
- 5 hand-picked failure examples with a one-line explanation each.

**Exit criteria**
- `results/eval_metrics.csv`, `results/error_breakdown.csv`, 3–4 charts in `results/figures/`.

---

## Phase 6 — Demo + README (Day 3, ~4 h)

**Do**
- `app.py` Gradio app styled per `DESIGN_SYSTEM.md`, deployed to HF Spaces.
- Upload FAISS index + id map + passages/sentences subset as HF dataset or Space files.
- Rate limiting + secrets per `SECURITY_AND_ACCESS.md`.
- README: pitch, architecture diagram, metrics table, charts, error breakdown, honest limitations, demo link.

**Exit criteria**
- Public demo URL works from a phone.
- Every number in README traceable to a file in `results/`.

---

## Stretch (only if all phases done)

- Cross-encoder re-ranker for sentence selection (`cross-encoder/ms-marco-MiniLM-L-6-v2`) — compare evidence recall.
- Second LLM size (8B vs 70B) — does a bigger model fix reasoning failures?
- Calibration: does the LLM's stated confidence match its accuracy?

## Cut list (don't build)

Streaming ingestion, RoBERTa triage classifier, user accounts, multi-agent orchestration, fine-tuning.
