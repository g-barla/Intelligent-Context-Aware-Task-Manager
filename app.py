
import os
from flask import Flask, render_template, request, redirect, url_for, flash
from db import init_db, add_task, list_tasks, complete_task, list_completed, reopen_task
from mcp_memory import Memory
from ai.priority_agent import prioritize_tasks
import csv, json 
from datetime import datetime, timezone

app = Flask(__name__)
app.secret_key = "dev-secret"

init_db()
memory = Memory()

def log_event(path: str, row: dict):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    new = not os.path.exists(path)
    with open(path, "a", newline="") as f:
        w = csv.DictWriter(f, fieldnames=row.keys())
        if new:
            w.writeheader()
        w.writerow(row)

@app.route("/", methods=["GET"])
def index():
    tasks = list_tasks()
    # prioritize_tasks now returns: (tasks, mode, provider, model)
    prioritized, mode, provider, model = prioritize_tasks(tasks, memory)

    
    try:
        log_event("logs/events.csv", {
            "ts": datetime.now(timezone.utc).isoformat(),
            "mode": mode,
            "provider": provider or "",
            "model": model or "",
            "rules": json.dumps(memory.rules()),
            "order": ",".join(str(t["task_id"]) for t in prioritized),
            "num_tasks": len(prioritized),
        })
    except Exception:
        pass
   

    return render_template(
        "index.html",
        tasks=prioritized,
        rules=memory.rules(),
        mode=mode,
        provider=provider,
        model=model
    )
@app.route("/add", methods=["POST"])
def add():
    desc = request.form.get("description", "").strip()
    deadline = request.form.get("deadline", "").strip()
    priority = request.form.get("priority", "3").strip()
    if not desc:
        flash("Description is required.", "error")
        return redirect(url_for("index"))
    add_task(desc, priority, deadline)
    flash("Task added.", "success")
    return redirect(url_for("index"))

@app.route("/complete/<int:task_id>", methods=["POST"])
def complete(task_id):
    # capture task details before it moves to 'completed' (for logging only)
    open_tasks = {t["task_id"]: t for t in list_tasks()}
    t = open_tasks.get(task_id)

    complete_task(task_id)
    memory.record_completion()
    flash("Task completed.", "success")

    # --- optional logging stays the same; remove if you don't want it ---
    try:
        from datetime import datetime, timezone
        now = datetime.now(timezone.utc)
        created = None
        age_days = ""
        if t and t.get("created_at"):
            created = t["created_at"]
            try:
                created_dt = datetime.fromisoformat(created.replace("Z", ""))
                age_days = round((now - created_dt).total_seconds() / 86400, 2)
            except Exception:
                age_days = ""
        from app import log_event  # if you defined it in the same file, this import is not needed
        log_event("logs/completions.csv", {
            "ts": now.isoformat(),
            "task_id": task_id,
            "priority": (t.get("priority") if t else ""),
            "has_deadline": bool(t.get("deadline")) if t else "",
            "age_days": age_days,
        })
    except Exception:
        pass
    # --------------------------------------------------------------------

    return redirect(url_for("index"))

@app.route("/settings", methods=["POST"])
def settings():
    prefer_deadline = request.form.get("prefer_deadline") == "on"
    prefer_high_priority = request.form.get("prefer_high_priority") == "on"
    memory.set_rule("prefer_deadline", prefer_deadline)
    memory.set_rule("prefer_high_priority", prefer_high_priority)
    flash("Preferences saved.", "success")
    return redirect(url_for("index"))

@app.route("/completed", methods=["GET"])
def completed():
    # Reuse the prioritizer just to discover current mode/provider/model for the badge
    open_tasks = list_tasks()
    _tmp, mode, provider, model = prioritize_tasks(open_tasks, memory)

    tasks = list_completed()
    return render_template("completed.html", tasks=tasks, mode=mode, provider=provider, model=model)

@app.route("/reopen/<int:task_id>", methods=["POST"])
def reopen(task_id):
    reopen_task(task_id)
    flash("Task moved back to Open.", "success")
    return redirect(url_for("completed"))
if __name__ == "__main__":
    app.run(debug=True)
