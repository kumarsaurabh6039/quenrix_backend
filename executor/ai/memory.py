# executor/ai/memory.py

SESSION_MEMORY = {}


def get_memory(session_id: str):
    if session_id not in SESSION_MEMORY:
        SESSION_MEMORY[session_id] = {
            # 🔹 NEW
            "history": [],

            # 🔹 OLD (unchanged)
            "mode": None,
            "current_topic": None,
            "last_question": None,
            "waiting_for_user": False
        }
    return SESSION_MEMORY[session_id]


def update_memory(session_id: str, updates: dict):
    memory = get_memory(session_id)
    memory.update(updates)
    SESSION_MEMORY[session_id] = memory


# 🔹 NEW (does NOT affect old logic)
def append_history(session_id: str, role: str, content: str):
    memory = get_memory(session_id)
    memory["history"].append({
        "role": role,
        "content": content
    })

    # keep memory bounded
    if len(memory["history"]) > 12:
        memory["history"] = memory["history"][-12:]
