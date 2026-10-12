# VeriCite — Multi-Hop Evidence-Grounded Fact Verification

**VeriCite** is a fact-verification system evaluated on the FEVER benchmark that checks factual claims against Wikipedia pages and returns verifiable verdicts (`SUPPORTS`, `REFUTES`, `NOT ENOUGH INFO`) with **exact sentence-level citations**.

---
# Hosted Link
https://huggingface.co/spaces/Niyati26/vericite

## 🔬 Core Contribution: Retrieval vs. Reasoning Error Breakdown

Most fact-checking RAG systems report only high-level accuracy. VeriCite explicitly categorizes failures:
- **Retrieval Failures**: The gold evidence was missed during the retrieval stage.
- **Reasoning Failures**: The evidence was retrieved and provided in the prompt, but the LLM failed to infer the correct verdict.

---

## 📊 Measured Benchmark Results (FEVER Dev Set)

All numbers are measured from our evaluation pipeline on 1,000 stratified FEVER dev claims:

### 1. Retrieval Performance (Passage-Level)

| Method | Recall@5 | Recall@10 | Recall@20 |
| :--- | :---: | :---: | :---: |
| **Dense (MiniLM-L6-v2 + FAISS FlatIP)** | 95.50% | 96.70% | 97.45% |
| **Sparse (BM25s)** | 94.74% | 95.95% | 96.70% |
| **Hybrid (Reciprocal Rank Fusion, k=60)** | **97.15%** | **97.60%** | **98.65%** |

*Hybrid fusion improves Recall@20 to 98.65%, reducing retrieval miss rate compared to either system alone.*

---

## 🛠️ Architecture & Pipeline Flow

```
Claim 
  ├─► Dense Retrieval (MiniLM-L6-v2 + FAISS) ──┐
  └─► Sparse Retrieval (BM25s) ────────────────┴─► Reciprocal Rank Fusion (k=60)
                                                        │
                                                        ▼
                                              Top-k Evidence Pages
                                                        │
                                                        ▼
                                              Sentence Selection (Cosine Sim)
                                                        │
                                                        ▼
                                              Llama 3.3 70B (Groq, Temp=0)
                                                        │
                                                        ▼
                                              Strict JSON Verdict + Citations
                                                        │
                                                        ▼
                                              Citation Faithfulness Gate
```

---

## 📂 Project Structure

- `data/` — Parquet tables processed with DuckDB & PyArrow (`pages.parquet`, `sentences.parquet`, `passages.parquet`, `eval_claims.parquet`)
- `results/` — Measured outputs (`retrieval_metrics.csv`, `eval_metrics.csv`)
- `results/figures/` — Generated benchmark charts (`error_breakdown.png`)
- `app.py` — Gradio interactive web application
