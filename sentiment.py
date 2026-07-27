# sentiment.py - Merkez bankasi para politikasi duygu analizi modulu
# Her merkez bankasinin PDF belgelerini okuyarak HAWKISH, DOVISH veya NEUTRAL siniflandirmasi uretir ve bu sonucu ana arayuze gonderir.

import os
from dotenv import load_dotenv
import chromadb
from sentence_transformers import SentenceTransformer
from openai import OpenAI
from query import get_foundry_endpoint


load_dotenv()


FOUNDRY_ENDPOINT = get_foundry_endpoint()


FOUNDRY_MODEL = os.getenv("FOUNDRY_MODEL", "phi-3.5-mini-instruct-trtrtx-gpu:2")
CHROMA_PATH   = os.getenv("CHROMA_PATH", "./chroma_db")
EMBED_MODEL   = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")




CENTRAL_BANKS = [
    {
        "key":      "Federal Reserve (FOMC)",
        "label":    "Fed",
        "currency": "USD",
        "flag":     "🇺🇸",
    },
    {
        "key":      "European Central Bank",
        "label":    "ECB",
        "currency": "EUR",
        "flag":     "🇪🇺",
    },
    {
        "key":      "Bank of England",
        "label":    "BoE",
        "currency": "GBP",
        "flag":     "🇬🇧",
    },
    {
        "key":      "Bank of Japan",
        "label":    "BoJ",
        "currency": "JPY",
        "flag":     "🇯🇵",
    },
    {
        "key":      "Reserve Bank of Australia",
        "label":    "RBA",
        "currency": "AUD",
        "flag":     "🇦🇺",
    },
    {
        "key":      "Reserve Bank of New Zealand",
        "label":    "RBNZ",
        "currency": "NZD",
        "flag":     "🇳🇿",
    },
    {
        "key":      "Bank of Canada",
        "label":    "BoC",
        "currency": "CAD",
        "flag":     "🇨🇦",
    },
    {
        "key":      "Swiss National Bank",
        "label":    "SNB",
        "currency": "CHF",
        "flag":     "🇨🇭",
    },
]



SENTIMENT_QUERY = (
    "interest rate decision inflation outlook monetary policy stance "
    "hawkish dovish rate hike cut hold"
)




def get_sentiment(bank_key: str, embedder, collection, llm_client) -> dict:

    query_vec = embedder.encode([SENTIMENT_QUERY]).tolist()
    results = collection.query(
        query_embeddings=query_vec,
        n_results=3,
        where={"category": {"$eq": bank_key}},
        include=["documents", "metadatas"],
    )

    chunks = results["documents"][0] if results["documents"] else []

    if not chunks:
        return {
            "sentiment": "N/A",
            "emoji":     "⚪",
            "summary":   "Belge bulunamadi.",
            "color":     "gray",
        }
    context = "\n\n".join(chunks)
    prompt = f"""Analyze the following central bank documents and determine their monetary policy stance.

Documents:
{context}

Respond with ONLY this exact format (nothing else):
STANCE: [HAWKISH or DOVISH or NEUTRAL]
REASON: [One short sentence in English, max 15 words]"""

    

    try:
        response = llm_client.chat.completions.create(
            model=FOUNDRY_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a monetary policy analyst. "
                        "Classify central bank stance as HAWKISH, DOVISH, or NEUTRAL. "
                        "Be concise. Never repeat words."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            max_tokens=60,
            temperature=0.1,
            extra_body={"repetition_penalty": 1.15},
        )


        raw = response.choices[0].message.content.strip()

        stance  = "NEUTRAL"

        summary = "Analiz tamamlandi."

        for line in raw.splitlines():
            line = line.strip()

            if line.upper().startswith("STANCE:"):
                val = line.split(":", 1)[1].strip().upper()
                if "HAWKISH" in val:
                    stance = "HAWKISH"
                elif "DOVISH" in val:
                    stance = "DOVISH"
                else:
                    stance = "NEUTRAL"
            elif line.upper().startswith("REASON:"):
                summary = line.split(":", 1)[1].strip()


        emoji_map = {"HAWKISH": "🦅", "DOVISH": "🕊️", "NEUTRAL": "⚖️"}
        color_map = {"HAWKISH": "red", "DOVISH": "green", "NEUTRAL": "orange"}

        return {
            "sentiment": stance,
            "emoji":     emoji_map.get(stance, "⚖️"),
            "summary":   summary,
            "color":     color_map.get(stance, "orange"),
        }

    except Exception as e:
        return {
            "sentiment": "ERROR",
            "emoji":     "❌",
            "summary":   str(e)[:60],
            "color":     "gray",
        }


def get_all_sentiments(embedder, collection, llm_client) -> list:

    results = []
    for bank in CENTRAL_BANKS:
        sentiment = get_sentiment(bank["key"], embedder, collection, llm_client)
        results.append({**bank, **sentiment})
    return results
