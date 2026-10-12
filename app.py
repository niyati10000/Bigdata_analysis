# app.py — VeriCite Interactive Demo (Hugging Face Spaces)
import os, json, time
import gradio as gr
from sentence_transformers import SentenceTransformer
import faiss
import numpy as np
from groq import Groq

# 1. Environment & Groq Client Setup
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None

embed_model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

# 2. Knowledge Base (FEVER-Aligned Wikipedia Passages)
SAMPLE_CORPUS = [
    {
        "page_id": "Barack_Obama",
        "title": "Barack Obama",
        "text": "Barack Hussein Obama II is an American politician who served as the 44th president of the United States from 2009 to 2017. A member of the Democratic Party, Obama was the first African-American president of the United States."
    },
    {
        "page_id": "Colin_Kaepernick",
        "title": "Colin Kaepernick",
        "text": "Colin Rand Kaepernick is an American civil rights activist and former football quarterback. He played six seasons for the San Francisco 49ers in the National Football League (NFL). In 2016, he knelt during the national anthem to protest police brutality."
    },
    {
        "page_id": "Earth",
        "title": "Earth",
        "text": "Earth is the third planet from the Sun and the only astronomical object known to harbor life. It orbits around the Sun in approximately 365.25 days."
    },
    {
        "page_id": "Apollo_11",
        "title": "Apollo 11",
        "text": "Apollo 11 was the American spaceflight that first landed humans on the Moon. Commander Neil Armstrong and lunar module pilot Buzz Aldrin landed the Apollo Lunar Module Eagle on July 20, 1969."
    },
    {
        "page_id": "Albert_Einstein",
        "title": "Albert Einstein",
        "text": "Albert Einstein was a German-born theoretical physicist who is widely held to be one of the greatest and most influential scientists of all time. Best known for developing the theory of relativity."
    },
    {
        "page_id": "Titanic",
        "title": "Titanic",
        "text": "The RMS Titanic was a British passenger liner operated by the White Star Line that sank in the North Atlantic Ocean on 15 April 1912 after striking an iceberg during her maiden voyage from Southampton to New York City."
    }
]

passages = [f"{item['title']}. {item['text']}" for item in SAMPLE_CORPUS]
corpus_embeddings = embed_model.encode(passages, normalize_embeddings=True).astype(np.float32)

index = faiss.IndexFlatIP(384)
index.add(corpus_embeddings)

# 3. Verification Pipeline
def verify_claim(claim: str):
    claim = claim.strip()
    if not claim or len(claim) < 5:
        return "⚠️ Please enter a claim with at least 5 characters.", "", ""
    
    t0 = time.time()
    
    # Retrieval
    claim_emb = embed_model.encode([claim], normalize_embeddings=True).astype(np.float32)
    scores, top_indices = index.search(claim_emb, k=2)
    
    retrieved = [SAMPLE_CORPUS[i] for i in top_indices[0]]
    ev_lines = [f"[{idx+1}] **{item['title']}**: {item['text']}" for idx, item in enumerate(retrieved)]
    evidence_display = "\n\n".join(ev_lines)
    
    retrieval_ms = round((time.time() - t0) * 1000, 1)
    
    if not client:
        return (
            "<div style='background-color:#e53e3e; color:white; padding:8px 16px; border-radius:6px; font-weight:bold;'>KEY MISSING</div>",
            "⚠️ **GROQ_API_KEY is not set.** Please add it in Hugging Face Space Settings -> Secrets.",
            evidence_display
        )
        
    t_llm = time.time()
    prompt = f"""You are an evidence-grounded fact verification system.
Verify this claim strictly against the provided evidence sentences.
Claim: "{claim}"

Evidence sentences:
{evidence_display}

Respond in JSON only:
{{"verdict": "SUPPORTS" | "REFUTES" | "NOT ENOUGH INFO", "explanation": "concise explanation under 40 words", "cited_ids": [1]}}"""

    try:
        resp = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0,
            response_format={"type": "json_object"},
            timeout=10.0
        )
        data = json.loads(resp.choices[0].message.content)
        verdict = data.get("verdict", "NOT ENOUGH INFO").upper()
        explanation = data.get("explanation", "")
        cited = data.get("cited_ids", [])
    except Exception as e:
        verdict = "ERROR"
        explanation = f"LLM error: {str(e)}"
        cited = []

    total_s = round(time.time() - t0, 2)
    
    color_map = {
        "SUPPORTS": "#38a169",
        "REFUTES": "#e53e3e",
        "NOT ENOUGH INFO": "#d69e2e",
        "ERROR": "#718096"
    }
    badge = f"<div style='background-color:{color_map.get(verdict, '#718096')}; color:white; padding:8px 16px; border-radius:6px; display:inline-block; font-weight:bold; font-size:18px;'>{verdict}</div>"
    
    timing_info = f"⏱️ *Latency: Retrieval {retrieval_ms}ms | Total {total_s}s*"
    explanation_display = f"### Explanation\n{explanation}\n\n**Cited Evidence Sentences:** {cited}\n\n{timing_info}"
    
    return badge, explanation_display, evidence_display

# 4. Gradio Interface
with gr.Blocks(title="VeriCite: Evidence-Grounded Fact Checking", theme=gr.themes.Soft()) as demo:
    gr.Markdown("# 🔍 VeriCite: FEVER Fact Verification")
    gr.Markdown("Verify factual claims against Wikipedia evidence with sentence-level citations.")
    
    with gr.Row():
        with gr.Column(scale=2):
            claim_input = gr.Textbox(
                label="Claim", 
                placeholder="e.g. Barack Obama was the 44th president of the United States.", 
                lines=2
            )
            submit_btn = gr.Button("Verify Claim", variant="primary")
            
            gr.Examples(
                examples=[
                    ["Barack Obama was the 44th president of the United States."],
                    ["Apollo 11 was an unmanned mission that crashed on Mars."],
                    ["The Titanic was a luxury train in Europe."],
                    ["Albert Einstein was born in 1980."]
                ],
                inputs=claim_input
            )
            
        with gr.Column(scale=3):
            verdict_output = gr.HTML(label="Verdict")
            explanation_output = gr.Markdown(label="Explanation & Citations")
            evidence_output = gr.Markdown(label="Retrieved Evidence Passages")

    submit_btn.click(
        fn=verify_claim,
        inputs=[claim_input],
        outputs=[verdict_output, explanation_output, evidence_output]
    )

if __name__ == "__main__":
    demo.launch()
