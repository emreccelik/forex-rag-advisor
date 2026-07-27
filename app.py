# app.py - Macroeconomic & Forex RAG Advisor ana Streamlit arayuzu
# Bu dosya tum gorsel bilesenleri bir araya getirir:
# Sol sidebar (sentiment paneli, filtre, ornek sorular) + ana chat alani
# Calistirmak icin: streamlit run app.py

import streamlit as st
from query import load_resources, answer
from sentiment import get_all_sentiments

st.set_page_config(
    page_title="Macro & Forex RAG Advisor",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)


st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&family=Inter:wght@400;500&display=swap');

.stApp {
    background: #070D1A;
    font-family: 'Inter', sans-serif;
    color: #CBD5E1;
}

[data-testid="stSidebar"] {
    background: #0B1629 !important;
    border-right: 1px solid #1E3A5F;
}
[data-testid="stSidebar"] * {
    color: #CBD5E1 !important;
}

.terminal-header {
    background: linear-gradient(135deg, #0B1629 0%, #0F2040 100%);
    border: 1px solid #1E3A5F;
    border-radius: 8px;
    padding: 20px 28px;
    margin-bottom: 20px;
    position: relative;
    overflow: hidden;
}

.terminal-header::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 2px;
    background: linear-gradient(90deg, #00D4AA, #3B82F6, #00D4AA);
    background-size: 200% 100%;
    animation: shimmer 3s infinite linear;
}

@keyframes shimmer {
    0% { background-position: -200% 0; }
    100% { background-position: 200% 0; }
}

.terminal-title {
    font-family: 'Space Grotesk', sans-serif;
    font-size: 26px;
    font-weight: 700;
    color: #F1F5F9;
    margin: 0 0 4px 0;
    letter-spacing: -0.5px;
}
.terminal-title span {
    color: #00D4AA;
}

.terminal-subtitle {
    font-family: 'JetBrains Mono', monospace;
    font-size: 12px;
    color: #64748B;
    letter-spacing: 0.5px;
}

.cursor {
    display: inline-block;
    width: 8px;
    height: 14px;
    background: #00D4AA;
    margin-left: 4px;
    vertical-align: middle;
    animation: blink 1.2s step-end infinite;
}
@keyframes blink {
    0%, 100% { opacity: 1; }
    50% { opacity: 0; }
}

.ticker-bar {
    display: flex;
    gap: 8px;
    flex-wrap: wrap;
    margin-top: 14px;
}
.ticker-chip {
    font-family: 'JetBrains Mono', monospace;
    font-size: 11px;
    font-weight: 500;
    padding: 3px 10px;
    border-radius: 4px;
    letter-spacing: 0.3px;
}

.ticker-hawkish { background: rgba(239,68,68,0.15); color: #F87171; border: 1px solid rgba(239,68,68,0.3); }
.ticker-dovish  { background: rgba(16,185,129,0.15); color: #34D399; border: 1px solid rgba(16,185,129,0.3); }
.ticker-neutral { background: rgba(245,158,11,0.15); color: #FCD34D; border: 1px solid rgba(245,158,11,0.3); }
.ticker-na      { background: rgba(100,116,139,0.15); color: #94A3B8; border: 1px solid rgba(100,116,139,0.3); }

.sent-card {
    background: #0F1E35;
    border: 1px solid #1E3A5F;
    border-radius: 8px;
    padding: 12px 14px;
    margin-bottom: 8px;
    transition: border-color 0.2s;
}
.sent-card:hover { border-color: #2D5A8E; }
.sent-bank {
    font-family: 'Space Grotesk', sans-serif;
    font-size: 13px;
    font-weight: 600;
    color: #F1F5F9;
}
.sent-currency {
    font-family: 'JetBrains Mono', monospace;
    font-size: 11px;
    color: #64748B;
    margin-left: 6px;
}
.sent-badge {
    font-family: 'JetBrains Mono', monospace;
    font-size: 11px;
    font-weight: 500;
    padding: 2px 8px;
    border-radius: 3px;
    display: inline-block;
    margin: 4px 0;
}
.badge-hawkish { background: rgba(239,68,68,0.15); color: #F87171; }
.badge-dovish  { background: rgba(16,185,129,0.15); color: #34D399; }
.badge-neutral { background: rgba(245,158,11,0.15); color: #FCD34D; }
.badge-na      { background: rgba(100,116,139,0.15); color: #94A3B8; }
.sent-reason {
    font-size: 11px;
    color: #64748B;
    margin-top: 2px;
    line-height: 1.4;
}

[data-testid="stChatMessage"] {
    background: #0F1E35 !important;
    border: 1px solid #1E3A5F !important;
    border-radius: 8px !important;
    margin-bottom: 8px !important;
}
[data-testid="stChatMessage"] p {
    color: #CBD5E1 !important;
    font-size: 14px !important;
    line-height: 1.7 !important;
}

[data-testid="stChatInput"] {
    background: #0F1E35 !important;
    border: 1px solid #1E3A5F !important;
    border-radius: 8px !important;
}
[data-testid="stChatInput"] textarea {
    background: transparent !important;
    color: #F1F5F9 !important;
    font-family: 'Inter', sans-serif !important;
}

.stButton > button {
    background: #0F2040 !important;
    border: 1px solid #1E3A5F !important;
    color: #CBD5E1 !important;
    border-radius: 6px !important;
    font-family: 'Inter', sans-serif !important;
    font-size: 12px !important;
    transition: all 0.2s !important;
}
.stButton > button:hover {
    border-color: #00D4AA !important;
    color: #00D4AA !important;
    background: rgba(0,212,170,0.08) !important;
}
.stButton > button[kind="primary"] {
    background: rgba(0,212,170,0.12) !important;
    border-color: #00D4AA !important;
    color: #00D4AA !important;
    font-weight: 600 !important;
}

[data-testid="stSelectbox"] > div > div {
    background: #0F1E35 !important;
    border-color: #1E3A5F !important;
    color: #CBD5E1 !important;
    border-radius: 6px !important;
}

[data-testid="stExpander"] {
    background: #0B1629 !important;
    border: 1px solid #1E3A5F !important;
    border-radius: 6px !important;
}

.source-tag {
    display: inline-block;
    font-family: 'JetBrains Mono', monospace;
    font-size: 11px;
    background: rgba(59,130,246,0.12);
    color: #60A5FA;
    border: 1px solid rgba(59,130,246,0.25);
    border-radius: 4px;
    padding: 2px 8px;
    margin: 2px 4px 2px 0;
}

.score-tag {
    font-family: 'JetBrains Mono', monospace;
    font-size: 10px;
    color: #475569;
}

.section-label {
    font-family: 'JetBrains Mono', monospace;
    font-size: 10px;
    color: #00D4AA;
    letter-spacing: 1.5px;
    text-transform: uppercase;
    margin-bottom: 8px;
}

hr { border-color: #1E3A5F !important; }

.disclaimer {
    font-family: 'JetBrains Mono', monospace;
    font-size: 10px;
    color: #334155;
    text-align: center;
    margin-top: 8px;
    padding: 6px;
    border-top: 1px solid #1E3A5F;
}
</style>
""", unsafe_allow_html=True)

@st.cache_resource
def get_resources():
    return load_resources()


@st.cache_data(ttl=1800, show_spinner=False)

def load_sentiments():
    embedder, collection, llm_client = get_resources()
    return get_all_sentiments(embedder, collection, llm_client)


with st.sidebar:
    st.markdown('<div class="section-label">▸ SENTIMENT PANEL</div>', unsafe_allow_html=True)
    st.caption("Automated analysis according to 2026 central bank reports.")
    if st.button("UPDATE ANALYSIS", use_container_width=True, type="primary"):
        st.cache_data.clear()
        st.rerun()
    try:
        sentiments = load_sentiments()
        badge_map = {
            "HAWKISH": ("badge-hawkish", "🦅 HAWKISH"),
            "DOVISH":  ("badge-dovish",  "🕊 DOVISH"),
            "NEUTRAL": ("badge-neutral", "⚖ NEUTRAL"),
        }
        for b in sentiments:
            cls, label = badge_map.get(b["sentiment"], ("badge-na", "— N/A"))
            st.markdown(f"""
            <div class="sent-card">
                <div>
                    <span class="sent-bank">{b['flag']} {b['label']}</span>
                    <span class="sent-currency">{b['currency']}</span>
                </div>
                <div class="sent-badge {cls}">{label}</div>
                <div class="sent-reason">{b['summary']}</div>
            </div>""", unsafe_allow_html=True)
    except Exception as e:
        st.error(f"Sentiment failed to load.: {e}")

    st.markdown("---")


    st.markdown('<div class="section-label">▸ FILTER</div>', unsafe_allow_html=True)
    category_options = [
        "All", "Federal Reserve (FOMC)", "European Central Bank",
        "Bank of England", "Bank of Japan", "Reserve Bank of Australia",
        "Reserve Bank of New Zealand", "Bank of Canada", "Swiss National Bank",
        "Economic Outlook", "Commodity Reports",
    ]
    selected_category = st.selectbox("Resource", category_options, label_visibility="collapsed")

    st.markdown("---")

    st.markdown('<div class="section-label">▸ Sample Questions</div>', unsafe_allow_html=True)
    examples = [
        "What are Fed's rate decisions in 2026?",
        "What is ECB's inflation outlook?",
        "How does BoJ assess Japan's economy?",
        "Compare Fed and ECB monetary policy",
        "How do central bank decisions affect forex?",
    ]
    for q in examples:
        if st.button(q, use_container_width=True):
            st.session_state["example_input"] = q
    st.markdown('<div class="disclaimer">This is not investment advice.<br>Phi-3.5 · Foundry Local · ChromaDB</div>', unsafe_allow_html=True)


try:
    sentiments = load_sentiments()
    ticker_html = '<div class="ticker-bar">'
    for b in sentiments:
        s = b["sentiment"]
        cls = {"HAWKISH": "ticker-hawkish", "DOVISH": "ticker-dovish", "NEUTRAL": "ticker-neutral"}.get(s, "ticker-na")
        ticker_html += f'<span class="ticker-chip {cls}">{b["flag"]} {b["label"]} · {s}</span>'
    ticker_html += "</div>"
except Exception:
    ticker_html = ""



st.markdown(f"""
<div class="terminal-header">
    <div class="terminal-title">📈 Macro & <span>Forex</span> RAG Advisor<span class="cursor"></span></div>
    <div class="terminal-subtitle">POWERED BY PHI-3.5 · FOUNDRY LOCAL · 2026 CENTRAL BANK REPORTS · {len(examples)} DEMO QUERIES READY</div>
    {ticker_html}
</div>
""", unsafe_allow_html=True)



if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg.get("sources"):
            with st.expander("📎 Kaynaklar"):
                for s in msg["sources"]:
                    st.markdown(
                        f'<span class="source-tag">{s["category"]}</span>'
                        f'<span class="source-tag">{s["source"]}</span>'
                        f'<span class="score-tag">  sim: {s["score"]}</span>',
                        unsafe_allow_html=True,
                    )




default_input = st.session_state.pop("example_input", "")
user_input = st.chat_input("Ask about macroeconomics or forex questions...") or default_input



if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    with st.chat_message("assistant"):
        with st.spinner("▸ Documents are scanning..."):
            try:
                embedder, collection, llm_client = get_resources()

                history = [
                    {"role": m["role"], "content": m["content"]}
                    for m in st.session_state.messages[:-1]
                ]

                reply, sources = answer(
                    user_input, embedder, collection, llm_client,
                    category_filter=selected_category,
                    chat_history=history,
                )

                st.markdown(reply)

                if sources:
                    with st.expander("📎 Resources"):
                        for s in sources:
                            st.markdown(
                                f'<span class="source-tag">{s["category"]}</span>'
                                f'<span class="source-tag">{s["source"]}</span>'
                                f'<span class="score-tag">  sim: {s["score"]}</span>',
                                unsafe_allow_html=True,
                            )
            except Exception as e:
                reply = f"❌ Error: {e}"
                sources = []
                st.error(reply)


    st.session_state.messages.append({
        "role": "assistant", "content": reply, "sources": sources
    })
