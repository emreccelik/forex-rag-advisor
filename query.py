# query.py - RAG soru-cevap motoru
# Kullanicidan gelen soruyu alir, ChromaDB'de ilgili PDF parcalarini arar,
# bulunan parcalari baglam olarak Phi-3.5'e gonderir ve cevap uretir.
# Multi-turn (cok turlu) sohbet desteklidir: model onceki konusmayi hatirlar.

import os
import json
import urllib.request
from dotenv import load_dotenv
import chromadb
from sentence_transformers import SentenceTransformer
from openai import OpenAI

load_dotenv()

FOUNDRY_MODEL = os.getenv("FOUNDRY_MODEL", "phi-3.5-mini-instruct-trtrtx-gpu:2")
CHROMA_PATH   = os.getenv("CHROMA_PATH", "./chroma_db")
EMBED_MODEL   = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")


def get_foundry_endpoint() -> str:
    
    import subprocess
    import re as _re

    try:
        result = subprocess.run(
            "foundry service status",
            capture_output=True, text=True, timeout=5, shell=True
        )
        output = result.stdout + result.stderr
        match = _re.search(r'http://[\d.]+:(\d+)', output)
        if match:
            port = match.group(1)
            endpoint = f"http://127.0.0.1:{port}/v1"
            _update_env_endpoint(endpoint)
            print(f"Foundry endpoint bulundu: {endpoint}")
            return endpoint
    except Exception:
        pass

    

    env_endpoint = os.getenv("FOUNDRY_ENDPOINT", "")
    if env_endpoint:
        try:
            url = env_endpoint.replace("/v1", "") + "/v1/models"
            urllib.request.urlopen(url, timeout=2)
            print(f"Mevcut endpoint calisiyor: {env_endpoint}")
            return env_endpoint
        except Exception:
            pass
        
    for port in [5273, 54172, 62236, 64401, 8080, 11434]:
        try:
            url = f"http://127.0.0.1:{port}/v1/models"
            urllib.request.urlopen(url, timeout=1)
            endpoint = f"http://127.0.0.1:{port}/v1"
            _update_env_endpoint(endpoint)
            print(f"Port taramasiyla bulundu: {endpoint}")
            return endpoint
        except Exception:
            continue

    fallback = os.getenv("FOUNDRY_ENDPOINT", "http://127.0.0.1:5273/v1")
    print(f"Endpoint bulunamadi, fallback: {fallback}")
    return fallback




def _update_env_endpoint(new_endpoint: str):
    env_path = os.path.join(os.path.dirname(__file__), ".env")
    try:
        with open(env_path, "r") as f:
            lines = f.readlines()
        with open(env_path, "w") as f:
            for line in lines:
                if line.startswith("FOUNDRY_ENDPOINT="):
                    f.write(f"FOUNDRY_ENDPOINT={new_endpoint}\n")
                else:
                    f.write(line)
    except Exception:
        pass


FOUNDRY_ENDPOINT = get_foundry_endpoint()
TOP_K = 5


def load_resources():
    embedder   = SentenceTransformer(EMBED_MODEL)
    chroma     = chromadb.PersistentClient(path=CHROMA_PATH)
    collection = chroma.get_collection("forex_rag")
    llm_client = OpenAI(base_url=FOUNDRY_ENDPOINT, api_key="foundry-local")
    return embedder, collection, llm_client




def retrieve(question: str, embedder, collection, category_filter: str = None, top_k: int = TOP_K):

    query_embedding = embedder.encode([question]).tolist()
    where = None
    if category_filter and category_filter not in ("All", "Tumu"):
        where = {"category": {"$eq": category_filter}}

    results = collection.query(
        query_embeddings=query_embedding,
        n_results=top_k,
        where=where,
        include=["documents", "metadatas", "distances"],
    )

    chunks    = results["documents"][0]
    metadatas = results["metadatas"][0]
    distances = results["distances"][0]

    return [
        {
            "text":     chunk,
            "source":   meta["source"],
            "category": meta["category"],
            "score":    round(1 - dist, 3),
        }
        for chunk, meta, dist in zip(chunks, metadatas, distances)
    ]





def build_system_prompt(context_chunks: list) -> str:
    context_text = ""
    for i, chunk in enumerate(context_chunks, 1):
        context_text += (
            f"\n[{i}] Source: {chunk['category']} - {chunk['source']}\n{chunk['text']}\n"
        )

    return (
        "You are a macroeconomic and forex analyst assistant. "
        "Answer questions using ONLY the provided source excerpts below. "
        "Be concise (3-5 sentences max). Mention which source supports each point. "
        "If sources lack enough info, say so briefly. Never repeat yourself. "
        "You remember the conversation history and can refer to previous questions and answers.\n\n"
        f"SOURCES:\n{context_text}"
    )



def answer(
    question: str,
    embedder,
    collection,
    llm_client,
    category_filter: str = None,
    chat_history: list = None,
):

    
    chunks = retrieve(question, embedder, collection, category_filter)

    if not chunks:
        return "No relevant information found in the documents for this question.", []

    system_prompt = build_system_prompt(chunks)
    messages = [{"role": "system", "content": system_prompt}]

    if chat_history:
        for msg in chat_history[-6:]:
            messages.append({"role": msg["role"], "content": msg["content"]})

    messages.append({"role": "user", "content": question})

    response = llm_client.chat.completions.create(
        model=FOUNDRY_MODEL,
        messages=messages,
        max_tokens=400,
        temperature=0.3,
        extra_body={"repetition_penalty": 1.15},
    )

    reply = response.choices[0].message.content
    return reply, chunks



if __name__ == "__main__":
    print("Kaynaklar yukleniyor...")
    embedder, collection, llm_client = load_resources()
    print("Hazir! Cikmak icin 'quit' yaz.\n")

    while True:
        question = input("Soru: ").strip()
        if question.lower() in ("quit", "exit"):
            break
        if not question:
            continue

        print("\nCevap uretiliyor...\n")
        reply, sources = answer(question, embedder, collection, llm_client)
        print(f"Cevap:\n{reply}\n")
        print("Kullanilan kaynaklar:")
        for s in sources:
            print(f"   - {s['category']} | {s['source']} (skor: {s['score']})")
        print()
