import os
from operator import itemgetter
from datetime import date
try:
    from openai import OpenAI
except Exception:
    OpenAI = None


def _days_left(deadline: str | None):
    if not deadline:
        return None
    try:
        y, m, d = map(int, deadline.split("-"))
        return (date(y, m, d) - date.today()).days
    except Exception:
        return None

def _build_reason(t, *, prefer_deadline: bool, prefer_high_priority: bool, mode_label: str):
    days = _days_left(t.get("deadline"))
    if days is None:
        due_txt = "no deadline"
    elif days < 0:
        due_txt = f"overdue by {abs(days)} days"
    elif days == 0:
        due_txt = "due today"
    else:
        due_txt = f"due in {days} days"
    pr_txt = f"P{t.get('priority')}"
    prefs = []
    if prefer_deadline: prefs.append("deadline")
    if prefer_high_priority: prefs.append("priority")
    pref_txt = "favored " + ", ".join(prefs) if prefs else "favored recency"
    # Keep it short (<= ~12 words) but informative
    return f"{mode_label}: {due_txt}; {pr_txt}; {pref_txt}"

def _heuristic_priority(tasks, memory):
    rules = memory.rules()
    prefer_deadline = rules.get("prefer_deadline", True)
    prefer_high_priority = rules.get("prefer_high_priority", True)

    # Build a sort key respecting the toggles
    def sort_key(t):
        # deadline: missing gets a very distant date so it drops last
        deadline = t.get("deadline") or "9999-12-31"
        pr = int(t.get("priority") or 3)
        created = t.get("created_at") or ""
        key = []
        if prefer_deadline:
            key.append(deadline)
        if prefer_high_priority:
            key.append(pr)
        key.append(created)
        return tuple(key)

        ordered = sorted(tasks, key=sort_key)

    # Per-task reason with deadline + priority (heuristic path)
    for t in ordered:
        t["reason"] = _build_reason(
            t,
            prefer_deadline=prefer_deadline,
            prefer_high_priority=prefer_high_priority,
            mode_label="Heuristic"
        )
    return ordered, "heuristic"

def _prompt(tasks, memory):
    rules = memory.rules()
    lines = [
        "You are an AI task prioritizer.",
        "Return ONLY compact JSON in priority order like:",
        '[{"id": 3, "why": "due in 2 days; P1; favored deadline"}, {"id": 1, "why": "no deadline; P2; favored priority"}]',
        f"User rules: prefer_deadline={rules.get('prefer_deadline')} prefer_high_priority={rules.get('prefer_high_priority')}",
        "Keep each 'why' SHORT (≤ 12 words) and include BOTH deadline status and priority.",
        "Tasks (id, desc, priority, days_until_deadline):"
    ]
    for t in tasks:
        dleft = _days_left(t.get("deadline"))
        dleft_str = "NA" if dleft is None else dleft
        lines.append(
            f'- id:{t["task_id"]} desc:{t["description"]} pr:P{t["priority"]} dleft:{dleft_str}'
        )
    return "\n".join(lines)

def _call_openai(prompt):
    """
    Prefer OpenRouter if OPENROUTER_API_KEY is set; otherwise use OpenAI if OPENAI_API_KEY is set.
    Uses a clean httpx client to avoid proxy env vars interfering.
    Returns (text, status, provider, model), where status in {"ok","quota","unauth","error","no_key"}.
    """
    try:
        from httpx import Client as HTTPXClient
        http_client = HTTPXClient(trust_env=False, timeout=30.0)
    except Exception:
        http_client = None

    provider = None
    model = None

    # --- Prefer OpenRouter (free-tier friendly) ---
    or_key = os.getenv("OPENROUTER_API_KEY")
    if or_key:
        from openai import OpenAI
        client = OpenAI(
            api_key=or_key,
            base_url="https://openrouter.ai/api/v1",
            http_client=http_client,
        )
        provider = "OpenRouter"
        model = os.getenv("MODEL_NAME", "meta-llama/llama-3.1-8b-instruct")

    else:
        # --- Fallback to OpenAI ---
        oa_key = os.getenv("OPENAI_API_KEY")
        if not oa_key:
            print("[AI] No API key found (neither OPENROUTER_API_KEY nor OPENAI_API_KEY). Using heuristic.")
            return None, "no_key", None, None
        from openai import OpenAI
        client = OpenAI(http_client=http_client)  # reads OPENAI_API_KEY from env
        provider = "OpenAI"
        model = os.getenv("MODEL_NAME", "gpt-4o-mini")

    try:
        resp = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
        )
        print(f"[AI] Received response from model: {model}")
        return resp.choices[0].message.content, "ok", provider, model
    except Exception as e:
        msg = str(e).lower()
        if "quota" in msg or "insufficient_quota" in msg:
            return None, "quota", provider, model
        if "unauthorized" in msg or "401" in msg:
            return None, "unauth", provider, model
        print(f"[AI] Call failed; falling back. Error: {e}")
        return None, "error", provider, model

def _apply_ai_order(tasks, ai_out, *, prefer_deadline=True, prefer_high_priority=True):
    """Parse the model output and reorder tasks; attach per-task reasons.
       Supports: [1,2,3] OR [{"id":1,"why":"..."}]. If 'why' missing, builds one reflecting user prefs."""
    import json, re
    m = re.search(r"\[.*\]", ai_out or "", re.S)
    if not m:
        return None

    try:
        arr = json.loads(m.group(0))
        if not arr:
            return None

        reasons = {}
        if isinstance(arr[0], dict) and "id" in arr[0]:
            order = {obj["id"]: i for i, obj in enumerate(arr)}
            reasons = {obj["id"]: (obj.get("why") or "").strip() for obj in arr}
        else:
            order = {tid: i for i, tid in enumerate(arr)}

        ordered = sorted(tasks, key=lambda t: order.get(t["task_id"], 10**9))

        for t in ordered:
            rid = t["task_id"]
            # Use AI-provided reason if present; otherwise build a concise fallback that includes deadline + priority
            if rid in reasons and reasons[rid]:
                t["reason"] = reasons[rid]
            else:
                t["reason"] = _build_reason(
                    t,
                    prefer_deadline=prefer_deadline,
                    prefer_high_priority=prefer_high_priority,
                    mode_label="AI"
                )
        return ordered
    except Exception:
        return None

def prioritize_tasks(tasks, memory):
    if not tasks:
        return [], "heuristic", None, None

    rules = memory.rules()
    prompt = _prompt(tasks, memory)
    ai_out, status, provider, model = _call_openai(prompt)

    if status == "ok" and ai_out:
        ordered = _apply_ai_order(
            tasks,
            ai_out,
            prefer_deadline=rules.get("prefer_deadline", True),
            prefer_high_priority=rules.get("prefer_high_priority", True),
        )
        if ordered:
            print("[AI] Using AI mode.")
            return ordered, "ai", provider, model

    print("[AI] Using heuristic mode.")
    ordered, _ = _heuristic_priority(tasks, memory)
    return ordered, "heuristic", provider, model