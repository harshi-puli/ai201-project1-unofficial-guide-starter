"""
app.py — Milestone 5: Gradio Interface
Runs the Berkeley Food Guide RAG chatbot at http://localhost:7860

Usage:
    pip install gradio
    python app.py
"""

import gradio as gr
from rag_query import ask

# ── Handler ───────────────────────────────────────────────────────────────────

def handle_query(question: str) -> tuple[str, str]:
    """Called by Gradio on every button click or Enter keypress."""
    if not question.strip():
        return "Please enter a question.", ""

    try:
        result  = ask(question)
        answer  = result["answer"]
        sources = "\n".join(f"• {s}" for s in result["sources"])
    except ValueError as e:
        # Missing API key or collection not built yet
        answer  = f"⚠️ Setup error: {e}"
        sources = ""
    except Exception as e:
        answer  = f"⚠️ Something went wrong: {e}"
        sources = ""

    return answer, sources


# ── UI ────────────────────────────────────────────────────────────────────────

with gr.Blocks(title="Berkeley Food Guide") as demo:

    gr.Markdown(
        """
        # 🐻 Berkeley Student Food Guide
        Ask anything about food near UC Berkeley — dining halls, restaurants,
        cafes, breakfast spots, vegan options, and more.
        *Answers are grounded in curated sources including the Daily Cal, Michelin Guide, and Berkeley Dining.*
        """
    )

    with gr.Row():
        with gr.Column(scale=3):
            inp = gr.Textbox(
                label       = "Your question",
                placeholder = "e.g. What are good vegan spots near campus?",
                lines       = 2,
            )
            btn = gr.Button("Ask", variant="primary")

    with gr.Row():
        with gr.Column(scale=3):
            answer_box = gr.Textbox(
                label = "Answer",
                lines = 8,
            )
        with gr.Column(scale=1):
            sources_box = gr.Textbox(
                label = "Sources",
                lines = 8,
            )

    # Example questions so users know what to ask
    gr.Examples(
        examples=[
            ["What dining hall has the most vegan options for dinner?"],
            ["What are some good breakfast spots near UC Berkeley?"],
            ["Recommend a high-end restaurant near Berkeley for a special occasion."],
            ["Where can I get good coffee and study near campus?"],
            ["Show me French cuisine near Berkeley."],
        ],
        inputs=inp,
    )

    # Wire up interactions
    btn.click(fn=handle_query, inputs=inp, outputs=[answer_box, sources_box])
    inp.submit(fn=handle_query, inputs=inp, outputs=[answer_box, sources_box])


if __name__ == "__main__":
    demo.launch()