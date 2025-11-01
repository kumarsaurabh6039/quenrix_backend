import json
import os
from dotenv import load_dotenv
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from openai import OpenAI

from courses.models import Courses, Subjects, Content
from batches.models import Batches
from users.models import Users

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


@csrf_exempt
def chatbot_view(request):
    if request.method != "POST":
        return JsonResponse({"error": "Invalid request"}, status=400)

    try:
        data = json.loads(request.body)
        user_message = data.get("message", "").strip().lower()

        if not user_message:
            return JsonResponse({"error": "Message is required."}, status=400)

        context_info = []

        # 🔹 Courses
        matched_courses = Courses.objects.filter(coursename__icontains=user_message)[:3]
        for c in matched_courses:
            context_info.append(f"Course: {c.coursename}")

        # 🔹 Subjects
        matched_subjects = Subjects.objects.filter(subjectname__icontains=user_message)[:3]
        for s in matched_subjects:
            context_info.append(f"Subject: {s.subjectname}")

        # 🔹 Content
        matched_contents = Content.objects.filter(contentname__icontains=user_message)[:3]
        for ct in matched_contents:
            context_info.append(f"Content: {ct.contentname}")

        # 🔹 Batches
        matched_batches = Batches.objects.filter(batchname__icontains=user_message)[:3]
        for b in matched_batches:
            context_info.append(f"Batch: {b.batchname}")

        # 🔹 Trainers (users)
        matched_trainers = Users.objects.filter(username__icontains=user_message)[:3]
        for t in matched_trainers:
            context_info.append(f"Trainer: {t.username}")

        # 🔹 Build system prompt
        if context_info:
            context_text = "\n".join(context_info)
        else:
            context_text = "No matching data found."

        system_prompt = (
            "You are a helpful assistant for an LMS (Learning Management System). "
            "Answer user questions using the provided context only. "
            "If no relevant data is found, politely say so.\n\n"
            f"Context:\n{context_text}"
        )

        # 🔹 Call OpenAI API
        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
        )

        reply = completion.choices[0].message.content

        return JsonResponse({"reply": reply, "context_used": context_info})

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
