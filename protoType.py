import os, json, html, gradio as gr
from letta_client import Letta

# ─────────────────── 1 · Connect / create agent ──────────────────────────────
BASE_URL = "http://localhost:8283"          # ← your Letta server
API_KEY  = os.getenv("LETTA_API_KEY")       # set var if on Letta Cloud
AGENT_ID = None                             # paste an existing ID to reuse

client = Letta(base_url=BASE_URL) if API_KEY is None else Letta(token=API_KEY)

if AGENT_ID is None:
    agent_state = client.agents.create(
        name="simple_agent",
        memory_blocks=[
            {"label": "human",   "value": "My name is Charles"},
            {"label": "persona", "value": "You are a helpful assistant and you always use emojis 🎉"}
        ],
        model="openai/gpt-4o-mini-2024-07-18",
        embedding="openai/text-embedding-3-small"
    )
    AGENT_ID = agent_state.id
else:
    agent_state = client.agents.retrieve(AGENT_ID)

# ─────────────────── 2 · Helper functions ────────────────────────────────────
def _bubble(text: str, css_class: str) -> str:
    """Wrap `text` in a coloured <div> with CSS class `css_class`."""
    return f'<div class="bubble {css_class}">{html.escape(text)}</div>'

def format_letta_messages(resp) -> list[str]:
    """
    Convert Letta’s batch reply into a sequence of HTML bubbles,
    preserving the original order.
    """
    bubbles = []
    for m in resp.messages:
        t = m.message_type
        if t == "assistant_message":
            bubbles.append(_bubble("🤖 " + m.content, "assistant"))
        elif t == "reasoning_message":
            bubbles.append(_bubble("🧠 " + m.reasoning, "reasoning"))
        elif t == "tool_call_message":
            details = f"{m.tool_call.name}\n```json\n{json.dumps(m.tool_call.arguments, indent=2)}\n```"
            bubbles.append(_bubble("🔧 " + details, "toolcall"))
        elif t == "tool_return_message":
            bubbles.append(_bubble("📦 " + json.dumps(m.tool_return, indent=2), "toolreturn"))
    return bubbles

# ─────────────────── 3 · Core chat function ──────────────────────────────────
def chat(user_input: str, chatbot_state: list[tuple[str, str]]):
    """Handle one user turn; returns (new_state, cleared_textbox)."""
    if not user_input.strip():
        return chatbot_state, ""

    # 1. send to Letta
    resp = client.agents.messages.create(
        agent_id=AGENT_ID,
        messages=[{"role": "user", "content": user_input}],
    )

    # 2. build HTML bubbles
    user_bubble   = _bubble("🗨️ " + user_input, "user")
    letta_bubbles = "".join(format_letta_messages(resp))

    # 3. push to Gradio Chatbot state
    chatbot_state.append((user_bubble, letta_bubbles))
    return chatbot_state, ""        # clear input box

# ─────────────────── 4 · Custom CSS ──────────────────────────────────────────
custom_css = """
/* ============ Chat bubbles ============ */
#chatbot .bubble{
  padding: 8px 12px;
  border-radius: .75rem;
  line-height: 1.35;
  white-space: pre-wrap;      /* keep line-breaks */
  font-size: 16px;
  color: #111;                /* << dark text that works on any light bg */
  max-width: 80%;
}

/* alignment + colours for each role */
#chatbot .bubble.user       { background:#9ecfff;  margin-left:auto; }  /* right */
#chatbot .bubble.assistant  { background:#fff5b1;  margin-right:auto; } /* left  */
#chatbot .bubble.reasoning  { background:#e5e5e5;  margin-right:auto;
                               font-style:italic;  opacity:.9; }
#chatbot .bubble.toolcall   { background:#c7ffd0;  margin-right:auto;
                               font-family:monospace; }
#chatbot .bubble.toolreturn { background:#ffdcb1;  margin-right:auto;
                               font-family:monospace; }
footer {display:none !important;}
"""


# ─────────────────── 5 · Build the Gradio interface ──────────────────────────
with gr.Blocks(css=custom_css, title="Letta Chat") as demo:
    gr.Markdown("## 💬 Chat with the Letta agent")

    # Height is now a constructor argument (no .style()!)
    chatbot = gr.Chatbot(elem_id="chatbot", height=450)

    txt = gr.Textbox(placeholder="Type here and hit Enter…")

    txt.submit(chat,  inputs=[txt, chatbot], outputs=[chatbot, txt])
    gr.Button("Send").click(chat, inputs=[txt, chatbot], outputs=[chatbot, txt])

# ─────────────────── 6 · Launch ──────────────────────────────────────────────
if __name__ == "__main__":
    demo.launch(share=False, server_port=7860)
