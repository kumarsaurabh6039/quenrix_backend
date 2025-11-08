import json
import os
from dotenv import load_dotenv
from rest_framework import generics
from .models import Exams, Questions, ExamAttempts, StudentAnswers, ExamResults, StudentBatches 
from .serializers import (
    ExamCreateSerializer, ExamResultDetailSerializer, ExamSerializer, QuestionSerializer, ExamAttemptSerializer,
    StudentAnswerSerializer, StudentBatchSerializer 
)

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.db import connection

from django.utils import timezone
from rest_framework import generics
from .models import Exams, ExamAttempts
from .serializers import ExamSerializer, ExamAttemptSerializer

from django.db.models import Q
from openai import OpenAI

# Create a client
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

class ExamListView(generics.ListAPIView):
    queryset = Exams.objects.all()
    serializer_class = ExamSerializer

class ExamDetailView(generics.RetrieveAPIView):
    queryset = Exams.objects.all()
    serializer_class = ExamSerializer
    lookup_field = 'examid'

class QuestionListView(generics.ListAPIView):
    serializer_class = QuestionSerializer

    def get_queryset(self):
        exam_id = self.kwargs['examid']
        return Questions.objects.filter(examid=exam_id)

class ExamAttemptCreateView(generics.CreateAPIView):
    queryset = ExamAttempts.objects.all()
    serializer_class = ExamAttemptSerializer

class StudentAnswerCreateView(generics.CreateAPIView):
    queryset = StudentAnswers.objects.all()
    serializer_class = StudentAnswerSerializer

class ExamResultListView(generics.ListAPIView):
    queryset = ExamResults.objects.all()
    serializer_class = ExamResultDetailSerializer

class EvaluateMCQAnswersView(APIView):
    def post(self, request, attempt_id):
        try:
            with connection.cursor() as cursor:
                cursor.execute("EXEC sp_evaluate_mcq_answers @attemptId = %s", [attempt_id])
                columns = [col[0] for col in cursor.description]
                row = cursor.fetchone()
                result = dict(zip(columns, row)) if row else {"message": "No result returned."}

            return Response(result, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class CalculateExamResultView(APIView):
    def post(self, request, attempt_id):
        try:
            with connection.cursor() as cursor:
                cursor.execute("EXEC sp_calculate_exam_results @attemptId = %s", [attempt_id])
                columns = [col[0] for col in cursor.description]
                row = cursor.fetchone()
                result = dict(zip(columns, row)) if row else {"message": "No result returned."}

            return Response(result, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        

class ExamCreateView(APIView):
    def post(self, request):
        serializer = ExamCreateSerializer(data=request.data)
        if serializer.is_valid():
            data = serializer.validated_data
            questions_json = json.dumps(data['questions'])

            try:
                with connection.cursor() as cursor:
                    cursor.execute("""
                        EXEC sp_create_exam_with_questions
                            @examName = %s,
                            @courseId = %s,
                            @batchId = %s,
                            @subjectId = %s,
                            @start = %s,
                            @end = %s,
                            @questions = %s
                    """, [
                        data.get('examName'),
                        data['courseId'],
                        data['batchId'],
                        data['subjectId'],
                        data['start'],
                        data['end'],
                        questions_json
                    ])
                    columns = [col[0] for col in cursor.description]
                    row = cursor.fetchone()
                    result = dict(zip(columns, row)) if row else {}

                return Response(result, status=status.HTTP_201_CREATED)

            except Exception as e:
                return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# 1️⃣ Exams for a student's course and batch
class StudentExamListView(generics.ListAPIView):
    serializer_class = ExamSerializer

    def get_queryset(self):
        course_id = self.kwargs['course_id']
        batch_id = self.kwargs['batch_id']
        now = timezone.now()

        # Optional query param: ?status=upcoming|ongoing|past
        status_filter = self.request.query_params.get('status', 'all')

        queryset = Exams.objects.filter(courseid=course_id, batchid=batch_id, is_active=True)

        if status_filter == 'upcoming':
            queryset = queryset.filter(start_datetime__gt=now)
        elif status_filter == 'ongoing':
            queryset = queryset.filter(start_datetime__lte=now, end_datetime__gte=now)
        elif status_filter == 'past':
            queryset = queryset.filter(end_datetime__lt=now)

        return queryset.order_by('start_datetime')


# 2️⃣ Get all attempts for a student (optional)
class StudentExamAttemptListView(generics.ListAPIView):
    serializer_class = ExamAttemptSerializer

    def get_queryset(self):
        user_id = self.kwargs['user_id']
        return ExamAttempts.objects.filter(userid=user_id).order_by('-attemptdate')


def evaluate_with_ai(question_text, student_answer, max_points):
    prompt = f"""
    Question: {question_text}
    Student Answer: {student_answer}

    Evaluate the student's answer.
    - Give a numeric score out of {max_points}.
    - Provide short feedback (1–2 sentences).
    Format:
    Score: <number>
    Feedback: <text>
    """

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}]
    )

    feedback_text = response.choices[0].message.content

    # Simple regex extraction for numeric score
    import re
    match = re.search(r"Score[:\-]?\s*(\d+)", feedback_text)
    score = int(match.group(1)) if match else 0

    # Ensure score doesn’t exceed max_points
    score = min(score, max_points)

    return score, feedback_text


class EvaluateAIDescriptiveCodingView(APIView):
    def post(self, request, attempt_id):
        try:
            # 🧠 Debugging info — to check what Django sees
            print("🔍 Total unevaluated answers:", StudentAnswers.objects.filter(evaluated=False).count())
            print("🔍 Unevaluated with descriptive answers:",
                  StudentAnswers.objects.filter(evaluated=False, descriptive_answer__isnull=False))

            # ✅ Fetch only descriptive/coding questions that are not yet evaluated and have content
            answers = StudentAnswers.objects.filter(
                attemptid=attempt_id,
                evaluated=False
            ).filter(
                Q(descriptive_answer__isnull=False) | Q(code_answer__isnull=False),
                questionid__questiontypeid__typename__in=['Descriptive', 'Coding']
            ).exclude(
                descriptive_answer=''
            ).exclude(
                code_answer=''
            )

            # 🧩 Check if anything found
            if not answers.exists():
                return Response({"message": "No unevaluated descriptive/coding answers found."},
                                status=status.HTTP_200_OK)

            total_descriptive_score = 0
            total_coding_score = 0

            for ans in answers:
                question_text = ans.questionid.questiontext
                student_answer = ans.descriptive_answer or ans.code_answer or ""
                max_points = ans.questionid.points or 0

                # 🧠 Call AI evaluation
                ai_score, ai_feedback = evaluate_with_ai(question_text, student_answer, max_points)

                # ✅ Update fields
                ans.ai_score = ai_score
                ans.ai_feedback = ai_feedback
                ans.points_earned = ai_score
                ans.evaluated = True
                ans.updated_at = timezone.now()
                ans.save()

                if ans.questionid.questiontypeid.typename == "Descriptive":
                    total_descriptive_score += ai_score
                elif ans.questionid.questiontypeid.typename == "Coding":
                    total_coding_score += ai_score

            # ✅ Update or create exam result entry
            result, created = ExamResults.objects.get_or_create(attemptid_id=attempt_id)
            result.total_descriptive_score = total_descriptive_score
            result.total_coding_score = total_coding_score
            result.save()

            return Response({
                "message": "AI evaluation complete",
                "total_descriptive_score": total_descriptive_score,
                "total_coding_score": total_coding_score
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class StudentFinalResultView(generics.ListAPIView):
    serializer_class = ExamResultDetailSerializer

    def get_queryset(self):
        user_id = self.kwargs['user_id']
        exam_id = self.kwargs.get('exam_id', None)

        queryset = ExamResults.objects.filter(
            attemptid__userid=user_id
        ).select_related('attemptid__examid')

        if exam_id:
            queryset = queryset.filter(attemptid__examid=exam_id)

        return queryset.order_by('-updated_at')

class StudentBatchByUserIdView(generics.ListAPIView):
    serializer_class = StudentBatchSerializer

    def get_queryset(self):
        user_id = self.kwargs['user_id'] 
        queryset = StudentBatches.objects.filter(
            userid_id=user_id 
        ).select_related('batchid') 

        return queryset