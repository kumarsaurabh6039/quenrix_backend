import json
from rest_framework import generics
from .models import Exams, Questions, ExamAttempts, StudentAnswers, ExamResults
from .serializers import (
    ExamCreateSerializer, ExamSerializer, QuestionSerializer, ExamAttemptSerializer,
    StudentAnswerSerializer, ExamResultSerializer
)

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.db import connection


from django.utils import timezone
from rest_framework import generics
from .models import Exams, ExamAttempts
from .serializers import ExamSerializer, ExamAttemptSerializer


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
    serializer_class = ExamResultSerializer

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
