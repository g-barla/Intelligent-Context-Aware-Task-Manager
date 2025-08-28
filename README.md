# 🧠 Intelligent Context-Aware Task Manager  

A lightweight productivity app that helps you decide **what to do next** and surfaces **the right context at the right time**. Built with Flask, SQLite, and AI-powered task prioritization + document retrieval.

---

## 📌 Project Summary  
This project tackles the everyday challenge of task overload:  
✅ Automatically orders your tasks by urgency, importance, and deadlines  
✅ Lets you attach PDFs/TXTs and instantly see relevant snippets (RAG)  
✅ Works entirely locally with a simple SQLite database  
✅ Clean, minimal Flask web interface  

---

## 💼 Why This Matters  
As our personal and work task lists grow, it becomes harder to:  
- Decide which task should come first  
- Remember the details buried across specs, notes, or reports  
- Switch contexts efficiently without losing time  

This app helps solve those by combining **AI + RAG (Retrieve-And-Generate)** with a simple, opinionated task manager.

---

## ⚙️ Tech Stack  

**Backend:** Python (Flask), SQLite  
**AI & RAG:** OpenRouter/OpenAI APIs, ChromaDB (vector store), SentenceTransformers embeddings  
**Frontend:** HTML (Jinja2 templates), CSS (vanilla, minimal styling)  
**Other:** PDF/TXT parsing, Python `csv` logs for analytics  

---

## 🔨 Key Features  

- **AI Prioritizer**  
  Orders tasks using an AI model (OpenRouter / OpenAI). If no API key is available, falls back to a heuristic based on deadline, priority, and recency.  

- **Task Memory**  
  Remembers user preferences like “prefer deadline” or “prefer high priority”.  

- **Task Lifecycle**  
  Add → View → Mark Completed → Reopen (all stored in SQLite).  

- **Attach Documents**  
  Upload PDFs or TXTs to tasks. Files are chunked, embedded, and indexed into ChromaDB.  

- **RAG Snippets**  
  When you open a task, you’ll see top 2–3 relevant snippets from attached documents. No hallucinations, just grounded retrieval.  

---

## 📊 Data Flow  

1. **User adds tasks** → stored in SQLite.  
2. **Prioritizer** → AI ranks or heuristic sorts tasks.  
3. **Upload a doc** → stored in `uploads/`, embedded into ChromaDB with task_id as namespace.  
4. **Open task** → `query_task` fetches top chunks, rendered as “Related snippets.”  

---

## 🚀 How to Run  

```bash
git clone https://github.com/g-barla/Intelligent-Context-Aware-Task-Manager
cd Intelligent-Context-Aware-Task-Manager
pip install -r requirements.txt
python app.py

