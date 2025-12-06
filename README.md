# 🧠 Multi-Workspace RAG System with Self-Evaluation  
*A fully local Retrieval-Augmented Generation pipeline with FAISS, Streamlit UI, automatic self-evaluation, and admin analytics.*

---

## 🚀 Overview

## 💬 Summary

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

self-eval-rag/
│── app.py # Streamlit UI
│── generator.py # Answer generation + self-evaluation
│── retriever.py # FAISS hybrid retriever
│── evaluator.py # LLM-based scoring engine
│── build_index.py # Workspace index builder
│── config.py # Centralized path resolver
│── data/<workspace>/ # PDF uploads
│── index/<workspace>/ # FAISS index + metadata
│── logs/<workspace>/ # Feedback logs
│── README.md


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



