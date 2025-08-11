
# Intelligent-Context-Aware-Task-Manager
=======
# Intelligent Context-Aware Task Manager (Phase 1)

An MVP that demonstrates:
- MCP-style memory to persist long-term task context (completion history, rules)
- AI prioritizer agent (OpenAI optional) with heuristic fallback
- SQLite storage for tasks
- Flask web UI (add/list/complete; AI prioritizes)

## Quickstart

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
# Optional AI:
# export OPENAI_API_KEY=sk-...
python app.py
# Open http://127.0.0.1:5000
```

