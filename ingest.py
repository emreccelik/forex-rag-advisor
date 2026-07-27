import os
import sys
from pathlib import Path
from dotenv import load_dotenv
import chromadb
from pypdf import PdfReader
from sentence_transformers import SentenceTransformer

load_dotenv()

DATA_PATH   = os.getenv("DATA_PATH", "./data")
CHROMA_PATH = os.getenv("CHROMA_PATH", "./chroma_db")
EMBED_MODEL = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")


CATEGORY_MAP = {
    "boe":       "Bank of England",
    "ecb":       "European Central Bank",
    "fomc":      "Federal Reserve (FOMC)",
    "outlook":   "Economic Outlook",
    "commodity": "Commodity Reports",
    "boj":       "Bank of Japan",
    "rba":       "Reserve Bank of Australia",
    "rbnz":      "Reserve Bank of New Zealand",
    "boc":       "Bank of Canada",
    "snb":       "Swiss National Bank",
}
CHUNK_SIZE    = 800
CHUNK_OVERLAP = 150




def extract_text(pdf_path: Path) -> str:
    reader = PdfReader(str(pdf_path))
    pages = []
    for page in reader.pages:
        text = page.extract_text()
        if text:
            pages.append(text.strip())
    return "\n\n".join(pages)





def chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[str]:
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        start += chunk_size - overlap
    return [c.strip() for c in chunks if len(c.strip()) > 100]



def main():

    print("Embedding modeli yukleniyor...")
    embedder = SentenceTransformer(EMBED_MODEL)
    print("ChromaDB baslatiliyor...")
    client = chromadb.PersistentClient(path=CHROMA_PATH)

    try:
        client.delete_collection("forex_rag")
        print("Eski koleksiyon silindi, yeniden olusturuluyor.")
    except Exception:
        pass
    collection = client.create_collection(
        name="forex_rag",
        metadata={"hnsw:space": "cosine"},
    )

    data_root = Path(DATA_PATH)
    if not data_root.exists():
        print(f"'{DATA_PATH}' klasoru bulunamadi. PDF'leri data/ altina koydugundan emin ol.")
        sys.exit(1)

    total_chunks = 0
    doc_id = 0


    for category_folder in sorted(data_root.iterdir()):
        if not category_folder.is_dir():
            continue
        
        category_key   = category_folder.name.lower()
        category_label = CATEGORY_MAP.get(category_key, category_folder.name)
        pdf_files      = list(category_folder.glob("*.pdf"))

        if not pdf_files:
            print(f"'{category_folder.name}' klasorunde PDF bulunamadi, atlaniyor.")
            continue

        print(f"\n{category_label} ({len(pdf_files)} dosya)")

        

        
        for pdf_path in pdf_files:
            print(f"   {pdf_path.name} isleniyor...", end=" ")
            try:
                text = extract_text(pdf_path)
                chunks = chunk_text(text)

                if not chunks:
                    print("Metin cikarilmadi, atlaniyor.")
                    continue
                
                embeddings = embedder.encode(chunks, show_progress_bar=False).tolist()

               
                ids       = [f"doc_{doc_id + i}" for i in range(len(chunks))]
                metadatas = [
                    {
                        "source":       pdf_path.name,
                        "category":     category_label,
                        "category_key": category_key,
                        "chunk_idx":    i,
                    }
                    for i in range(len(chunks))
                ]

               
                collection.add(
                    ids=ids,
                    embeddings=embeddings,
                    documents=chunks,
                    metadatas=metadatas,
                )

                doc_id       += len(chunks)
                total_chunks += len(chunks)
                print(f"{len(chunks)} chunk")

            except Exception as e:
                print(f"Hata: {e}")

    print(f"\nTamamlandi! Toplam {total_chunks} chunk ChromaDB'ye yuklendi.")
    print(f"   Koleksiyon yolu: {CHROMA_PATH}")


if __name__ == "__main__":
    main()
