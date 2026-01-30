from openai import OpenAI
from django.conf import settings

from .prompts import CODEXA_SYSTEM_PROMPT
from .memory import get_memory, update_memory, append_history
from .intent import detect_reply_type

client = OpenAI(api_key=settings.OPENAI_API_KEY)


def codexa_chat(session_id: str, message: str, context: str = ""):
    memory = get_memory(session_id)

    # ---- Mode detection ----
    if context.strip():
        update_memory(session_id, {"mode": "debugging"})
    elif "why" in message.lower() or "how" in message.lower():
        update_memory(session_id, {"mode": "teaching"})
    else:
        update_memory(session_id, {"mode": "thinking"})

    memory = get_memory(session_id)

    system_prompt = f"""
{CODEXA_SYSTEM_PROMPT}

Conversation State:
- Mode: {memory['mode']}
- Topic: {memory['current_topic']}
- Last Question: {memory['last_question']}
- Waiting For User: {memory['waiting_for_user']}
""".strip()

    if memory["waiting_for_user"]:
        system_prompt += (
            "\nThe student is answering your last question. "
            "Continue from it. Do NOT change topic."
        )

    messages = [{"role": "system", "content": system_prompt}]
    messages.extend(memory["history"][-6:])

    messages.append({
        "role": "user",
        "content": f"""
Context:
{context}

Student:
{message}
""".strip()
    })

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
        temperature=0.4,
        max_tokens=500
    )

    reply = response.choices[0].message.content.strip()

    # ---- Persist history ----
    append_history(session_id, "user", message)
    append_history(session_id, "assistant", reply)

    # ---- Question tracking ----
    if reply.endswith("?") and len(reply.split()) < 20:
        update_memory(session_id, {
            "last_question": reply,
            "waiting_for_user": True
        })
    else:
        update_memory(session_id, {"waiting_for_user": False})

    # ---- Topic inference ----
    if memory["current_topic"] is None:
        msg = message.lower()
        if "loop" in msg:
            update_memory(session_id, {"current_topic": "loop logic"})
        elif "array" in msg:
            update_memory(session_id, {"current_topic": "array traversal"})
        elif "recursion" in msg:
            update_memory(session_id, {"current_topic": "recursion"})

    # ✅ INTENT DETECTION (KEY FIX)
    reply_type = detect_reply_type(message, reply)

    return reply, reply_type
