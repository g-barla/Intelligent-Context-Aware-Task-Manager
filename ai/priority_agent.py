
import os
from operator import itemgetter

try:
    from openai import OpenAI
except Exception:
    OpenAI = None

def _heuristic_priority(tasks, memory):
    def sort_key(t):
        deadline = t.get("deadline") or "9999-12-31"
        pr = t.get("priority") or 3
        created = t.get("created_at") or ""
        return (deadline, pr, created)
    return sorted(tasks, key=sort_key)

def _prompt(tasks, memory):
    rules = memory.rules()
    lines = [
        "You are an AI task prioritizer. Return a JSON array of task_ids in recommended order.",
        f"Rules: prefer_deadline={rules.get('prefer_deadline')}, prefer_high_priority={rules.get('prefer_high_priority')}",
        "Tasks:",
    ]
    for t in tasks:
        lines.append(f"- id:{t['task_id']} desc:{t['description']} pr:{t['priority']} deadline:{t['deadline']} created:{t['created_at']}")
    return "\n".join(lines)

def _call_openai(prompt):
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key or OpenAI is None:
        return None
    client = OpenAI(api_key=api_key)
    try:
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
        )
        return resp.choices[0].message.content
    except Exception:
        return None

def prioritize_tasks(tasks, memory):
    if not tasks:
        return []
    prompt = _prompt(tasks, memory)
    ai_out = _call_openai(prompt)
    if ai_out:
        import json, re
        try:
            m = re.search(r"\[.*\]", ai_out, re.S)
            if m:
                arr = json.loads(m.group(0))
                order = {tid: i for i, tid in enumerate(arr)}
                return sorted(tasks, key=lambda t: order.get(t['task_id'], 1e9))
        except Exception:
            pass
    return _heuristic_priority(tasks, memory)
