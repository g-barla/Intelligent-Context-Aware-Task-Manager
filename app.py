
import os
from flask import Flask, render_template, request, redirect, url_for, flash
from db import init_db, add_task, list_tasks, complete_task, list_completed, reopen_task
from mcp_memory import Memory
from ai.priority_agent import prioritize_tasks

app = Flask(__name__)
app.secret_key = "dev-secret"

init_db()
memory = Memory()

@app.route("/", methods=["GET"])
def index():
    tasks = list_tasks()
    prioritized = prioritize_tasks(tasks, memory)
    return render_template("index.html", tasks=prioritized, rules=memory.rules())

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
    complete_task(task_id)
    memory.record_completion()
    flash("Task completed.", "success")
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
    tasks = list_completed()
    return render_template("completed.html", tasks=tasks)

@app.route("/reopen/<int:task_id>", methods=["POST"])
def reopen(task_id):
    reopen_task(task_id)
    flash("Task moved back to Open.", "success")
    return redirect(url_for("completed"))
if __name__ == "__main__":
    app.run(debug=True)
