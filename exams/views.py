import json
import os
import re
from dotenv import load_dotenv
from decimal import Decimal 
from openai import OpenAI
from django.db import connection
from django.db.models import Q, Sum 
from django.utils import timezone

# --- REST Framework Imports ---
from rest_framework import generics
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

# --- Local Models Imports ---
from .models import (
    Exams, Questions, ExamAttempts, StudentAnswers, ExamResults, 
    StudentBatches, Options, QuestionTypes 
) 

# --- Serializers ---
from .serializers import (
    ExamCreateSerializer, ExamResultDetailSerializer, ExamSerializer, QuestionSerializer, 
    ExamAttemptSerializer, StudentAnswerSerializer, StudentBatchSerializer 
)

# --- Configuration ---
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


# =========================================================================================
# === CORE EVALUATION FUNCTIONS ===
# =========================================================================================

def evaluate_mcq_orm(attempt_id):
    """Evaluates MCQ answers and updates StudentAnswers records."""
    mcq_answers = StudentAnswers.objects.filter(
        attemptid=attempt_id,
        selectedoptionid__isnull=False 
    ).select_related('questionid', 'selectedoptionid')

    for answer in mcq_answers:
        is_correct = False
        try:
            # Check if student's selection matches the correct option (iscorrect=True)
            Options.objects.get(
                optionid=answer.selectedoptionid.optionid, 
                iscorrect=True 
            )
            is_correct = True
        except Options.DoesNotExist:
            is_correct = False

        question_points = Decimal(answer.questionid.points or 0)
        points_earned = question_points if is_correct else Decimal(0)
        
        answer.is_correct = is_correct
        answer.points_earned = points_earned
        answer.evaluated = True 
        answer.updated_at = timezone.now()
        answer.save()
        
    # Mark unanswered MCQs as evaluated with 0 points
    StudentAnswers.objects.filter(
        attemptid=attempt_id,
        selectedoptionid__isnull=True, 
        questionid__questiontypeid=1 
    ).update(points_earned=Decimal(0), evaluated=True)
    
    return True

def evaluate_with_ai(question_text, student_answer, max_points):
    """Evaluates descriptive/coding answers using AI."""
    
    if not student_answer or student_answer.strip() == "":
        return 0.0, "No answer provided by the student."

    prompt = f"""
    Question: {question_text}
    Student Answer: {student_answer}

    Evaluate the student's answer.
    - Give a numeric score out of {max_points}. The score must not exceed {max_points}.
    - Provide short feedback (1–2 sentences).
    Format:
    Score: <number>
    Feedback: <text>
    """

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}]
        )

        feedback_text = response.choices[0].message.content
        match = re.search(r"Score[:\-]?\s*(\d+(\.\d+)?)", feedback_text) 
        score = float(match.group(1)) if match else 0.0

    except Exception as e:
        print(f"OpenAI API Error: {e}")
        return 0.0, "AI evaluation failed due to API error."

    score = max(0.0, min(score, max_points))

    return score, feedback_text

# =========================================================================================
# === DJANGO VIEWS ===
# =========================================================================================

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
        return Questions.objects.filter(examid=exam_id).select_related('questiontypeid') 

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
            evaluate_mcq_orm(attempt_id)
            return Response({"message": "MCQ evaluation complete."}, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class CalculateExamResultView(APIView):
    def post(self, request, attempt_id):
        try:
            total_score_data = StudentAnswers.objects.filter(
                attemptid=attempt_id
            ).aggregate(
                total_earned=Sum('points_earned')
            )
            final_score = total_score_data.get('total_earned') or Decimal(0)
            
            final_attempt = ExamAttempts.objects.get(attemptid=attempt_id)
            final_attempt.total_score = final_score
            final_attempt.save()

            with connection.cursor() as cursor:
                cursor.execute("EXEC sp_calculate_exam_results @attemptId = %s", [attempt_id])

            return Response({"Message": "Exam results updated successfully.", "total_score": final_score}, status=status.HTTP_200_OK)

        except ExamAttempts.DoesNotExist:
            return Response({"error": f"Attempt ID {attempt_id} not found."}, status=status.HTTP_404_NOT_FOUND)
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


class StudentExamListView(generics.ListAPIView):
    serializer_class = ExamSerializer

    def get_queryset(self):
        course_id = self.kwargs['course_id']
        batch_id = self.kwargs['batch_id']
        now = timezone.now()

        status_filter = self.request.query_params.get('status', 'all')

        queryset = Exams.objects.filter(courseid=course_id, batchid=batch_id, is_active=True)

        if status_filter == 'upcoming':
            queryset = queryset.filter(start_datetime__gt=now)
        elif status_filter == 'ongoing':
            queryset = queryset.filter(start_datetime__lte=now, end_datetime__gte=now)
        elif status_filter == 'past':
            queryset = queryset.filter(end_datetime__lt=now)

        return queryset.order_by('start_datetime')


class StudentExamAttemptListView(generics.ListAPIView):
    serializer_class = ExamAttemptSerializer

    def get_queryset(self):
        user_id = self.kwargs['user_id']
        return ExamAttempts.objects.filter(userid=user_id).order_by('-attemptdate')


class EvaluateAIDescriptiveCodingView(APIView):
    # This endpoint is deprecated, all logic is in EvaluateCompleteExamView
    def post(self, request, attempt_id):
        return Response({"message": "This endpoint is now deprecated. Use evaluate-complete/."}, status=status.HTTP_200_OK)


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
class StudentAnswerDetailListView(APIView):
    """Retrieves detailed student answers including AI score and feedback for an attempt."""
    def get(self, request, attempt_id):
        try:
            queryset = StudentAnswers.objects.filter(
                attemptid=attempt_id,
                questionid__questiontypeid__in=[2, 3] 
            ).select_related('questionid')

            results = []
            for answer in queryset:
                if answer.evaluated and (answer.descriptive_answer or answer.code_answer):
                    results.append({
                        'questionid': answer.questionid.questionid,
                        'question_text': answer.questionid.questiontext,
                        'question_type_id': answer.questionid.questiontypeid_id,
                        'student_answer': answer.descriptive_answer or answer.code_answer or "No answer submitted.",
                        'ai_score': float(answer.ai_score) if answer.ai_score else 0.0,
                        'ai_feedback': answer.ai_feedback or "AI feedback not available.",
                        'points_earned': float(answer.points_earned) if answer.points_earned else 0.0,
                        'max_points': answer.questionid.points
                    })
            
            return Response(results, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    

class EvaluateCompleteExamView(APIView):
    def post(self, request, attempt_id):
        try:
            # === Step 1: Evaluate MCQs ===
            evaluate_mcq_orm(attempt_id)
            
            # === Step 2: Evaluate Descriptive & Coding (AI) ===
            
            # Filter for non-evaluated answers (False or null) that have text/code content
            answers = StudentAnswers.objects.filter(
                attemptid=attempt_id
            ).filter(
                Q(evaluated=False) | Q(evaluated__isnull=True)
            ).filter(
                Q(descriptive_answer__isnull=False) | Q(code_answer__isnull=False),
                questionid__questiontypeid__in=[2, 3] # Type 2: Descriptive, 3: Coding
            ).exclude(
                descriptive_answer=''
            ).exclude(
                code_answer=''
            ).select_related('questionid', 'questionid__questiontypeid')


            total_descriptive_score = Decimal(0)
            total_coding_score = Decimal(0)

            for ans in answers:
                question_text = ans.questionid.questiontext
                student_answer = ans.descriptive_answer or ans.code_answer or ""
                max_points = ans.questionid.points or 0

                ai_score, ai_feedback = evaluate_with_ai(question_text, student_answer, max_points)

                try:
                    ai_score_decimal = Decimal(ai_score)
                except Exception:
                    ai_score_decimal = Decimal(0)

                ans.ai_score = ai_score_decimal
                ans.ai_feedback = ai_feedback
                ans.points_earned = ai_score_decimal
                ans.evaluated = True
                ans.updated_at = timezone.now()
                ans.save()
                
                question_type_id = ans.questionid.questiontypeid_id
                if question_type_id == 2:
                    total_descriptive_score += ai_score_decimal
                elif question_type_id == 3:
                    total_coding_score += ai_score_decimal
                
            # Update ExamResults with partial scores
            result_obj, _ = ExamResults.objects.get_or_create(attemptid_id=attempt_id)
            result_obj.total_descriptive_score = total_descriptive_score
            result_obj.total_coding_score = total_coding_score
            result_obj.updated_at = timezone.now()
            result_obj.save()


            # === Step 3: Finalize Result Calculation ===
            
            total_score_data = StudentAnswers.objects.filter(
                attemptid=attempt_id
            ).aggregate(
                total_earned=Sum('points_earned')
            )
            final_score = total_score_data.get('total_earned') or Decimal(0)
            
            # Update ExamAttempts with final score
            try:
                final_attempt = ExamAttempts.objects.get(attemptid=attempt_id)
                final_attempt.total_score = final_score
                final_attempt.save()
            except ExamAttempts.DoesNotExist:
                return Response({"error": f"Attempt ID {attempt_id} not found during final scoring."}, status=status.HTTP_404_NOT_FOUND)

            with connection.cursor() as cursor:
                cursor.execute("EXEC sp_calculate_exam_results @attemptId = %s", [attempt_id])
            
            # Calculate Max Score
            max_score_qs = Questions.objects.filter(examid=final_attempt.examid_id)
            max_score_data = max_score_qs.aggregate(Sum('points'))
            max_score = max_score_data.get('points__sum') or 0
            max_score_int = int(max_score)

            return Response({
                "attemptid": final_attempt.attemptid,
                "total_score": final_score, 
                "max_score": max_score_int,
                "status_message": f"Results processed. Score: {final_score:.2f}/{max_score_int}"
            }, status=status.HTTP_200_OK)

        except Exception as e:
            print(f"CRITICAL EVALUATION ERROR: {e}")
            return Response({"error": "Full evaluation process failed.", "detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)