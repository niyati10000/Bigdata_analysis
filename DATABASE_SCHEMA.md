# DATABASE_SCHEMA.md — data tables

There is no database server. Every "table" is a Parquet file under `/kaggle/working/data/` (or `demo_assets/` on the Space). Spark writes them; pandas/pyarrow reads them.

**No `users` table — on purpose.** The demo has no accounts. Nothing is stored per person. Rate limiting uses an in-memory IP counter that is never written to disk. Adding users means adding auth, a privacy policy, and data-retention rules — none of which help this project.

---

## Source data (read-only, from FEVER)

### `pages.parquet`
| column | type | notes |
|---|---|---|
| page_id | string | raw FEVER id, e.g. `Barack_Obama`, `Colin_Kaepernick`. **Primary key** |
| title | string | display version: underscores → spaces, `-LRB-` → `(`, `-RRB-` → `)` |
| text | string | intro section |
| n_sentences | int | |

### `sentences.parquet`
| column | type | notes |
|---|---|---|
| page_id | string | FK → pages |
| sent_id | int | line number from FEVER `lines` field |
| text | string | sentence text (tab-separated hyperlink anchors stripped) |

Primary key: (page_id, sent_id). Partition by first character of page_id for fast lookup.

### `passages.parquet`
| column | type | notes |
|---|---|---|
| row_idx | int64 | position in the embedding matrix. **Primary key** |
| page_id | string | FK → pages |
| passage | string | `title + ". " + intro`, truncated to ~128 tokens |

### `claims.parquet`
| column | type | notes |
|---|---|---|
| claim_id | int64 | FEVER `id`. **Primary key** |
| split | string | `train` / `dev` |
| claim | string | |
| label | string | `SUPPORTS` / `REFUTES` / `NOT ENOUGH INFO` |

### `evidence_gold.parquet`
| column | type | notes |
|---|---|---|
| claim_id | int64 | FK → claims |
| evidence_set_id | int | one claim can have several alternative sets; any one complete set is enough |
| page_id | string | |
| sent_id | int | |

NEI claims have no rows here.

### `eval_claims.parquet`
Subset of `claims` — 1,000 dev rows, stratified by label, seed 42. Same columns. **Never regenerate once results exist.**

---

## Index artifacts

| file | what |
|---|---|
| `emb/shard_XXXX.npy` | fp16, shape (n, 384), rows aligned to `passages.row_idx` |
| `faiss.index` | IVF-PQ index; FAISS id == `row_idx` |
| `faiss_id_map.parquet` | `row_idx → page_id` (two columns) |
| `bm25/` | bm25s saved index; doc order == `row_idx` |

---

## Results (written by eval cells)

### `retrieval_results.parquet`
| column | type |
|---|---|
| claim_id | int64 |
| method | string (`dense` / `bm25` / `hybrid`) |
| top_pages | list<string> (top 20, ranked) |
| top_sentences | list<struct<page_id, sent_id, score>> (top 5) |
| page_hit_at_5 / _10 / _20 | bool |
| evidence_hit_at_5 | bool |
| latency_ms | float |

### `verdicts.parquet`
| column | type | notes |
|---|---|---|
| claim_id | int64 | |
| condition | string | `with_evidence` / `no_evidence` |
| model | string | exact LLM model name |
| prompt_hash | string | sha256, links to cache |
| raw_response | string | |
| verdict | string | parsed |
| explanation | string | |
| cited_ids | list<int> | valid ones only |
| invented_ids | list<int> | cited but not given → hallucination |
| parse_ok | bool | |
| latency_ms | float | |
| input_tokens / output_tokens | int | |

### `llm_cache/` 
One JSON file per `prompt_hash`. Makes reruns free and crash-safe.

### CSVs in `results/`
- `retrieval_metrics.csv` — method × recall@k
- `eval_metrics.csv` — condition × {label_acc, fever_score, macro_f1, citation_faithfulness, parse_fail_rate}
- `error_breakdown.csv` — wrong verdicts split into retrieval_failure / reasoning_failure, per label
