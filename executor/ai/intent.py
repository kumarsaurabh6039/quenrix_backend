def detect_reply_type(user_message: str, assistant_reply: str) -> str:
    msg = user_message.lower().strip()
    reply = assistant_reply.lower().strip()

    # Explicit user intents
    question_intents = [
        "give me a question",
        "generate a question",
        "coding question",
        "practice problem",
        "interview question",
        "change the question",
        "another question",
        "new question",
        "question on",
        "question about"
    ]

    if any(msg.startswith(k) or k in msg for k in question_intents):
        return "question"

    # Assistant-generated question patterns
    if (
        reply.startswith("let's try this coding question")
        or reply.startswith("how about this question")
        or reply.startswith("sure! how about")
        or reply.startswith("write a function")
    ):
        return "question"

    return "chat"
