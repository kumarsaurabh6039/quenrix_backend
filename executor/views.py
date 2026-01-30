import subprocess
import tempfile
import os

from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

from executor.ai.llm import codexa_chat

LANGUAGE_CONFIG = {
    "python": {"extension": ".py", "command": ["python"]},
    "javascript": {"extension": ".js", "command": ["node"]},
    "cpp": {
        "extension": ".cpp",
        "compile": ["g++", "{file}", "-o", "{exe}"],
        "run": ["{exe}"]
    }
}


@api_view(["POST"])
def execute_code(request):
    language = request.data.get("language")
    code = request.data.get("code")

    if language not in LANGUAGE_CONFIG:
        return Response({"error": "Unsupported language"}, status=400)

    try:
        config = LANGUAGE_CONFIG[language]

        with tempfile.TemporaryDirectory() as tmpdir:
            source_path = os.path.join(tmpdir, f"main{config['extension']}")
            with open(source_path, "w") as f:
                f.write(code)

            if language == "cpp":
                exe_path = os.path.join(tmpdir, "a.out")
                compile_cmd = [
                    arg.format(file=source_path, exe=exe_path)
                    for arg in config["compile"]
                ]
                compile_proc = subprocess.run(
                    compile_cmd, capture_output=True, text=True
                )
                if compile_proc.returncode != 0:
                    return Response({"stderr": compile_proc.stderr})
                run_cmd = [exe_path]
            else:
                run_cmd = config["command"] + [source_path]

            proc = subprocess.run(
                run_cmd, capture_output=True, text=True, timeout=5
            )

            return Response({
                "stdout": proc.stdout,
                "stderr": proc.stderr,
                "exit_code": proc.returncode
            })

    except subprocess.TimeoutExpired:
        return Response({"error": "Execution timed out"}, status=408)
    except Exception as e:
        return Response({"error": str(e)}, status=500)


@api_view(["POST"])
def codexa_chat_view(request):
    session_id = request.data.get("session_id", "default")
    message = request.data.get("message", "")
    code = request.data.get("code", "")
    question = request.data.get("question", "")

    if not message:
        return Response(
            {"error": "message is required"},
            status=status.HTTP_400_BAD_REQUEST
        )

    context = f"""
Question:
{question}

User Code:
{code}
""".strip()

    reply, reply_type = codexa_chat(
        session_id=session_id,
        message=message,
        context=context
    )

    return Response({
        "reply": reply,
        "type": reply_type
    })
