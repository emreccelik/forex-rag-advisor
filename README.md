2026 yilina ait merkez bankasi raporlari ve ekonomik gorunum belgelerine dayali, yerel RAG (Retrieval-Augmented Generation) mimarisiyle calisan bir AI danisman uygulamasi.
PDF'ler  pypdf  Chunking  sentence-transformers (embedding) ChromaDB Kullanici Sorusu Embedding ChromaDB (retrieval) Phi-3.5 (Foundry Local) Cevap


LLM (cevap uretme) = Phi-3.5-mini (Azure AI Foundry Local) 
Embedding = sentence-transformers (all-MiniLM-L6-v2) 
Vektor DB = ChromaDB 
PDF okuma = pypdf 
Arayuz = Streamlit 

`data/fomc/`     = Fed (FOMC) toplanti tutanaklari
`data/ecb/`      = Avrupa Merkez Bankasi raporlari
`data/boe/`      = Bank of England raporlari
`data/boj/`      = Bank of Japan raporlari
`data/rba/`      = Reserve Bank of Australia raporlari
`data/rbnz/`     = Reserve Bank of New Zealand raporlari
`data/boc/`      = Bank of Canada raporlari
`data/snb/`      = Swiss National Bank raporlari
`data/outlook/`  = Genel ekonomik gorunum raporlari
`data/commodity/`= Emtia raporlari

Gereksinimler
- Python 3.10+
- Azure AI Foundry Local
- Phi-3.5-mini modeli (`foundry model run phi-3.5-mini`)


python -m venv venv
venv\Scripts\activate 
pip install -r requirements.txt

foundry service start

FOUNDRY_ENDPOINT degerini `foundry service status` cikintisiyla guncelleyebilirsin.

python ingest.py

streamlit run app.py

