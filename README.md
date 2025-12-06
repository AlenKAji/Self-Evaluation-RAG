# 🧠 Multi-Workspace RAG System with Self-Evaluation  
*A fully local Retrieval-Augmented Generation pipeline with FAISS, Streamlit UI, automatic self-evaluation, and admin analytics.*

---

## 🚀 Overview

This project evolved from a basic RAG experiment into a polished **production-ready RAG system** featuring:

- Evaluation-driven answer correction  
- Multi-workspace support  
- Interactive UI  
- Feedback analytics  
- Clean environment handling  

It demonstrates strong understanding of RAG engineering, retrieval pipelines, embeddings, LLM prompting, and modern Python application design.

---

## 🧩 Features

### 🔍 Hybrid RAG Retrieval
- Uses **SentenceTransformers (MiniLM-L6-v2)** for embeddings  
- Stores vectors in a **FAISS IndexFlatL2** database  
- Chunking + metadata storage for clean context retrieval  

### 🤖 Local LLM Reasoning
- Answers generated using **Gemma models** running locally via Ollama (`gemma3:1b`)  
- Context-only answering enforcement to minimize hallucination  

### 🧪 Self-Evaluation Engine
Each answer is automatically rated on:
- **Factual Accuracy**
- **Completeness**
- **Reasoning Quality**
- **Confidence Score**

If the score is below threshold → the system **regenerates** intelligently.

### 🗂 Multi-Workspace Architecture
Each workspace has its own:
- data/(workspace)/
- index/(workspace)/
- logs/(workspace)/


This allows:
- Multiple users  
- Multiple projects  
- Fully isolated knowledge bases  

### 📚 Streamlit UI
Tabs include:
- 📄 Upload PDFs  
- 💬 Ask Questions  
- 📊 Admin Dashboard  

### 🔐 Admin Dashboard
Admin can view:
- Logged Q&A  
- User feedback trends  
- Evaluation scores  
- Workspace analytics  

---

## 🛠️ Technologies Used

| Component | Technology |
|-----------|------------|
| Embeddings | SentenceTransformers |
| Vector DB | FAISS |
| LLM | Gemma (via Ollama) |
| Backend | Python |
| Frontend | Streamlit |
| Evaluation | Custom JSON-scored LLM |
| File Processing | PyPDF2 |

---

## 📁 Project Structure
```
Self-Evaluation-RAG/
├─ app.py                         # Streamlit UI (workspaces, Q&A, admin dashboard)
├─ build_index.py                 # Builds FAISS index for a given workspace from PDFs
├─ config.py                      # Central config + workspace path resolver
├─ generator.py                   # RAG answer generation + self-correcting loop
├─ retriever.py                   # Hybrid retriever over FAISS + metadata
├─ evaluator.py                   # LLM-based evaluation (scores accuracy, completeness, etc.)
├─ reranker.py                    # (Optional) Reranking of contexts before generation
├─ requirements.txt               # Python dependencies
├─ README.md                      # Project documentation
│
├─ data/                          # Root data folder (per-workspace subfolders)
│  └─ default/
│     └─ <your_pdfs_here>.pdf
│
├─ index/                         # Root index folder (per-workspace FAISS indices)
│  └─ default/
│     ├─ faiss_index.bin          # FAISS vector index
│     └─ metadata.json            # Chunk metadata (source file, text, etc.)
│
├─ logs/                          # Root logs folder (per-workspace logs)
│  └─ default/
│     └─ feedback_log.jsonl       # User feedback + evaluation logs (JSONL)
│
└─ ragenv312/                     # (local virtualenv – do NOT commit to git)
   └─ ...                         # site-packages, Scripts, etc.

```
---

## 🧑‍💻 What I Learned

### 1️⃣ Embedding Models & Vector Databases  
- Using SentenceTransformers  
- Creating FAISS indices  
- Metadata mapping for contextual retrieval  

### 2️⃣ Document Processing  
- PDF extraction (PyPDF2)  
- Chunking strategies (overlap, size tuning)  
- Handling malformed text  

### 3️⃣ LLM Integration & Prompting  
- Running **Gemma locally**  
- Context-controlled answer generation  
- Regeneration loops for higher accuracy  

### 4️⃣ Self-Evaluation Pipelines  
- Designing scoring rubrics  
- Parsing and validating LLM JSON output  
- Using scores as control signals  

### 5️⃣ Multi-Workspace System Design  
- Dynamic folder management  
- Lazy module loading  
- Scalable multi-user RAG setup  

### 6️⃣ Front-End Development  
- Streamlit interactivity  
- Tabbed UI  
- Admin login & dashboards  
- PDF upload + index rebuild automation  

### 7️⃣ Robust Engineering  
- Error handling  
- Unicode-safe console output  
- Cleaning stale indexes  
- Modular code structure  

---

## 🧪 Results

### ✅ Fully functional local RAG system
Uses PDFs as the only knowledge source — no hallucinations when data is missing.

### 📈 Better reliability via self-evaluation
Automatically retries if accuracy or completeness is low.

### 🗂 Clean workspace separation  
Each project has its own saved index + logs.

### 🧠 Admin insights
Feedback tracking + evaluation metrics reveal system performance.

### ⚡ Fast vector search  
FAISS returns top chunks within milliseconds.

### 🌐 User-friendly interface  
Upload → Index → Ask → Evaluate → Improve.

---

## 🧭 Future Improvements

- Add streaming responses from Ollama  
- Integrate BGE reranker for higher retrieval precision  
- Implement SQLite or MongoDB for logs  
- Add user authentication (multi-user login)  


---




