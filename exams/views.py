import json
import os
import re
from dotenv import load_dotenv
from decimal import Decimal
from openai import OpenAI
from django.db import connection
from django.db.models import Q, Sum, Count
from django.utils import timezone

# --- REST Framework Imports ---
from rest_framework import generics
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny

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


def evaluate_mcq_orm(attempt_id):
    """Evaluates MCQ answers and updates StudentAnswers records."""
    mcq_answers = StudentAnswers.objects.filter(
        attemptid=attempt_id,
        selectedoptionid__isnull=False
    ).select_related('questionid', 'selectedoptionid')

    for answer in mcq_answers:
        is_correct = False
        try:
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
    """
    Evaluates descriptive/coding answers using AI.
    Returns a tuple of (score, feedback, model_answer).
    model_answer is always generated so it can be shown to students who skipped
    or answered incorrectly.
    """

    no_answer = not student_answer or student_answer.strip() == ""

    if no_answer:
        # Student did not attempt — skip scoring but still generate a model answer.
        prompt = f"""
Question: {question_text}

The student did not provide an answer.

Please provide a concise, well-structured model answer for this question
(3–5 sentences or key bullet points, suitable for a student to learn from).

Format your response exactly as:
Model Answer: <your model answer here>
"""
        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}]
            )
            raw = response.choices[0].message.content or ""
            match = re.search(r"Model Answer[:\-]?\s*([\s\S]+)", raw)
            model_answer = match.group(1).strip() if match else raw.strip()
        except Exception as e:
            print(f"OpenAI API Error (model answer for no-answer): {e}")
            model_answer = "Model answer could not be generated."
        return 0.0, "No answer provided by the student.", model_answer

    # Student submitted an answer — evaluate and also return a model answer.
    prompt = f"""
Question: {question_text}
Student Answer: {student_answer}

Evaluate the student's answer.
1. Give a numeric score out of {max_points}. The score must not exceed {max_points}.
2. Provide short constructive feedback (1–2 sentences).
3. Provide a concise model answer (3–5 sentences or key points) that a student
   can learn from, regardless of whether the student got it right or wrong.

Format your response exactly as:
Score: <number>
Feedback: <text>
Model Answer: <text>
"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}]
        )
        raw = response.choices[0].message.content or ""

        score_match    = re.search(r"Score[:\-]?\s*(\d+(\.\d+)?)", raw)
        feedback_match = re.search(r"Feedback[:\-]?\s*(.*?)(?=\nModel Answer[:\-]?|\Z)", raw, re.DOTALL)
        model_match    = re.search(r"Model Answer[:\-]?\s*([\s\S]+)", raw)

        score        = float(score_match.group(1)) if score_match else 0.0
        feedback     = feedback_match.group(1).strip() if feedback_match else raw.strip()
        model_answer = model_match.group(1).strip() if model_match else ""

    except Exception as e:
        print(f"OpenAI API Error: {e}")
        return 0.0, "AI evaluation failed due to API error.", ""

    score = max(0.0, min(score, max_points))
    return score, feedback, model_answer


# =========================================================================================
# === DJANGO VIEWS ===
# =========================================================================================

class ExamListView(generics.ListAPIView):
    serializer_class = ExamSerializer

    def get_queryset(self):
        now = timezone.now()
        # This ensures the 'exam-list/' route ONLY returns upcoming and ongoing active exams
        return Exams.objects.filter(is_active=True, end_datetime__gte=now).order_by('start_datetime')


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


class StudentExamListView(APIView):
    def get(self, request, course_id, batch_id):
        status_filter = request.query_params.get('status', 'all')
        try:
            with connection.cursor() as cursor:
                base_sql = """
                    SELECT
                        e.examId        AS examid,
                        e.examName      AS examname,
                        e.start_datetime,
                        e.end_datetime,
                        e.is_active,
                        e.courseId      AS courseid,
                        e.batchId       AS batchid,
                        e.subjectId     AS subjectid,
                        b.batchName     AS batch_name,
                        s.subjectName   AS subject_name,
                        (SELECT COUNT(*) FROM questions q WHERE q.examId = e.examId) AS total_questions
                    FROM exams e
                    LEFT JOIN batches b ON e.batchId = b.batchId
                    LEFT JOIN subjects s ON e.subjectId = s.subjectId
                    WHERE e.courseId = %s AND e.batchId = %s AND e.is_active = 1
                """
                now = timezone.now()
                params = [course_id, batch_id]
                if status_filter == 'upcoming':
                    base_sql += ' AND e.start_datetime > %s'
                    params.append(now)
                elif status_filter == 'ongoing':
                    base_sql += ' AND e.start_datetime <= %s AND e.end_datetime >= %s'
                    params.extend([now, now])
                elif status_filter == 'past':
                    base_sql += ' AND e.end_datetime < %s'
                    params.append(now)
                base_sql += ' ORDER BY e.start_datetime'
                cursor.execute(base_sql, params)
                columns = [col[0] for col in cursor.description]
                data = [dict(zip(columns, row)) for row in cursor.fetchall()]
            return Response(data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'detail': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# =========================================================
# NEW API: Fetches ONLY Active (Ongoing + Upcoming) Exams
# =========================================================
class ActiveStudentExamListView(APIView):
    """
    Fetches exams that are currently active and have NOT ended yet.
    Completely filters out old/past exams at the database level.
    """
    def get(self, request, course_id, batch_id):
        try:
            with connection.cursor() as cursor:
                now = timezone.now()
                cursor.execute("""
                    SELECT
                        e.examId        AS examid,
                        e.examName      AS examname,
                        e.start_datetime,
                        e.end_datetime,
                        e.is_active,
                        e.courseId      AS courseid,
                        e.batchId       AS batchid,
                        e.subjectId     AS subjectid,
                        b.batchName     AS batch_name,
                        s.subjectName   AS subject_name,
                        (SELECT COUNT(*) FROM questions q WHERE q.examId = e.examId) AS total_questions
                    FROM exams e
                    LEFT JOIN batches b ON e.batchId = b.batchId
                    LEFT JOIN subjects s ON e.subjectId = s.subjectId
                    WHERE e.courseId = %s
                      AND e.batchId = %s
                      AND e.end_datetime >= %s
                      AND (e.is_active = 1 OR e.is_active IS NULL)
                    ORDER BY e.start_datetime
                """, [course_id, batch_id, now])
                columns = [col[0] for col in cursor.description]
                data = [dict(zip(columns, row)) for row in cursor.fetchall()]
            return Response(data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'detail': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


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
    """
    Returns ALL questions for an attempt with:
    - MCQ: all options, which student selected, which is correct
    - Descriptive/Coding: student answer, AI score, AI feedback
    - Improvement tips per question based on performance
    """
    def get(self, request, attempt_id):
        try:
            # Get the attempt to find the exam
            attempt = ExamAttempts.objects.select_related('examid').get(attemptid=attempt_id)

            # Get all questions for this exam, ordered
            all_questions = Questions.objects.filter(
                examid=attempt.examid
            ).select_related('questiontypeid').order_by('questionid')

            # Get all student answers for this attempt, keyed by questionid
            all_answers = StudentAnswers.objects.filter(
                attemptid=attempt_id
            ).select_related('questionid', 'selectedoptionid')

            answered_map = {ans.questionid.questionid: ans for ans in all_answers}

            results = []

            for idx, question in enumerate(all_questions):
                q_id = question.questionid
                q_type = question.questiontypeid_id  # 1=MCQ, 2=Descriptive, 3=Coding
                max_pts = question.points or 0
                answer = answered_map.get(q_id)

                item = {
                    'questionid': q_id,
                    'question_number': idx + 1,
                    'question_text': question.questiontext,
                    'question_type_id': q_type,
                    'max_points': max_pts,
                    'points_earned': 0.0,
                    'is_correct': False,
                    'student_answer': None,
                    'correct_answer': None,
                    'ai_score': None,
                    'ai_feedback': None,
                    'model_answer': None,
                    'options': [],
                    'selected_option_id': None,
                    'correct_option_id': None,
                    'improvement_tip': None,
                }

                if q_type == 1:  # MCQ
                    # Fetch all options for this question
                    options = list(Options.objects.filter(questionid=question))
                    correct_opt = next((o for o in options if o.iscorrect), None)

                    item['options'] = [
                        {
                            'optionid': opt.optionid,
                            'optiontext': opt.optiontext,
                            'iscorrect': bool(opt.iscorrect),
                        }
                        for opt in options
                    ]

                    if correct_opt:
                        item['correct_answer'] = correct_opt.optiontext
                        item['correct_option_id'] = correct_opt.optionid

                    if answer and answer.selectedoptionid:
                        item['selected_option_id'] = answer.selectedoptionid.optionid
                        item['student_answer'] = answer.selectedoptionid.optiontext
                        item['is_correct'] = bool(answer.is_correct)
                        item['points_earned'] = float(answer.points_earned) if answer.points_earned is not None else 0.0
                    else:
                        # Not attempted
                        item['student_answer'] = None
                        item['is_correct'] = False
                        item['points_earned'] = 0.0

                    # Improvement tip for MCQ
                    if not item['is_correct']:
                        if item['student_answer'] is None:
                            item['improvement_tip'] = "You skipped this question. Always attempt every question — even an educated guess can earn marks."
                        else:
                            item['improvement_tip'] = (
                                f"You selected an incorrect option. The correct answer was: \"{item['correct_answer']}\". "
                                "Review this topic and practice similar questions to strengthen your understanding."
                            )
                    else:
                        item['improvement_tip'] = "Great job! You answered this correctly. Keep revising to maintain your accuracy."

                elif q_type in [2, 3]:  # Descriptive or Coding
                    q_label = "descriptive" if q_type == 2 else "coding"

                    if answer:
                        raw_answer = answer.descriptive_answer or answer.code_answer or ""
                        item['student_answer'] = raw_answer if raw_answer.strip() else None
                        item['ai_score'] = float(answer.ai_score) if answer.ai_score is not None else 0.0
                        item['points_earned'] = float(answer.points_earned) if answer.points_earned is not None else 0.0
                        item['is_correct'] = item['points_earned'] > 0

                        # Parse stored ai_feedback — it may contain an embedded model answer.
                        raw_feedback = answer.ai_feedback or "AI evaluation is pending."
                        if "[MODEL_ANSWER]" in raw_feedback:
                            parts = raw_feedback.split("[MODEL_ANSWER]\n", 1)
                            item['ai_feedback'] = parts[0].strip()
                            stored_model_answer = parts[1].strip()
                        else:
                            item['ai_feedback'] = raw_feedback
                            stored_model_answer = None

                        # Show model answer only when the student skipped or didn't fully score.
                        score_ratio = item['points_earned'] / max_pts if max_pts > 0 else 0
                        if item['student_answer'] is None or score_ratio < 1.0:
                            item['model_answer'] = stored_model_answer
                        else:
                            item['model_answer'] = None

                        # Improvement tip based on score ratio
                        if item['student_answer'] is None:
                            item['improvement_tip'] = (
                                f"You did not attempt this {q_label} question. "
                                "Even a partial answer can earn partial credit. Practice writing structured responses."
                            )
                        elif score_ratio == 0:
                            item['improvement_tip'] = (
                                f"Your {q_label} answer did not meet the evaluation criteria. "
                                "Review the key concepts and try to structure your answer clearly next time."
                            )
                        elif score_ratio < 0.5:
                            item['improvement_tip'] = (
                                f"You earned {item['points_earned']:.1f}/{max_pts} points. "
                                "Your answer was partially correct. Focus on completeness and depth in your responses."
                            )
                        elif score_ratio < 1.0:
                            item['improvement_tip'] = (
                                f"Good effort! You scored {item['points_earned']:.1f}/{max_pts}. "
                                "With a little more detail and precision, you can achieve full marks."
                            )
                        else:
                            item['improvement_tip'] = "Excellent! Full marks on this question. Your answer was comprehensive and accurate."
                    else:
                        # No StudentAnswers record at all — generate a model answer on-the-fly
                        # so the student can still learn what was expected.
                        item['student_answer'] = None
                        item['points_earned'] = 0.0
                        item['is_correct'] = False
                        item['ai_feedback'] = "No answer was submitted for this question."
                        item['improvement_tip'] = (
                            f"You did not submit an answer for this {q_label} question. "
                            "Always attempt every question for a chance at partial credit."
                        )
                        try:
                            _, _, live_model_answer = evaluate_with_ai(
                                question.questiontext, "", max_pts
                            )
                            item['model_answer'] = live_model_answer if live_model_answer else None
                        except Exception:
                            item['model_answer'] = None

                results.append(item)

            return Response(results, status=status.HTTP_200_OK)

        except ExamAttempts.DoesNotExist:
            return Response({'detail': f'Attempt ID {attempt_id} not found.'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            import traceback
            print(f"StudentAnswerDetailListView Error: {traceback.format_exc()}")
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class EvaluateCompleteExamView(APIView):
    def post(self, request, attempt_id):
        try:
            # === Step 1: Evaluate MCQs ===
            evaluate_mcq_orm(attempt_id)

            # === Step 2: Evaluate Descriptive & Coding (AI) ===
            answers = StudentAnswers.objects.filter(
                attemptid=attempt_id
            ).filter(
                Q(evaluated=False) | Q(evaluated__isnull=True)
            ).filter(
                Q(descriptive_answer__isnull=False) | Q(code_answer__isnull=False),
                questionid__questiontypeid__in=[2, 3]
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

                ai_score, ai_feedback, model_answer = evaluate_with_ai(question_text, student_answer, max_points)

                try:
                    ai_score_decimal = Decimal(ai_score)
                except Exception:
                    ai_score_decimal = Decimal(0)

                # Embed the model answer inside ai_feedback using a delimiter so it
                # can be extracted later without requiring a new database column.
                combined_feedback = ai_feedback
                if model_answer:
                    combined_feedback += f"\n\n[MODEL_ANSWER]\n{model_answer}"

                ans.ai_score = ai_score_decimal
                ans.ai_feedback = combined_feedback
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
                final_attempt.ai_evaluated = True
                final_attempt.updated_at = timezone.now()
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
                "total_score": float(final_score),
                "max_score": max_score_int,
                "status_message": f"Results processed. Score: {final_score:.2f}/{max_score_int}"
            }, status=status.HTTP_200_OK)

        except Exception as e:
            import traceback
            print(f"CRITICAL EVALUATION ERROR: {traceback.format_exc()}")
            return Response({"error": "Full evaluation process failed.", "detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)


# =========================================================================================
# ADDED: ForceCompleteExamView
#
# Purpose:
#   When a student closes the browser tab or loses internet mid-exam,
#   the Angular frontend calls navigator.sendBeacon() in the window:beforeunload event.
#   sendBeacon() cannot attach Authorization headers, so this endpoint has
#   permission_classes = [AllowAny] — no token required.
#
#   This view evaluates only the MCQ answers that were already saved,
#   calculates the total score, and marks the attempt as complete.
#   AI evaluation (descriptive/coding) is intentionally skipped here because
#   sendBeacon has a very short timeout and OpenAI calls take too long.
#   AI evaluation will run later if the student reopens and views their result.
#
# Called by:
#   POST /api/exams/force-complete/
#   Body: { "attemptId": 123 }
# =========================================================================================
class ForceCompleteExamView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        attempt_id = request.data.get('attemptId')

        if not attempt_id:
            return Response(
                {'error': 'attemptId is required.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            attempt = ExamAttempts.objects.get(attemptid=attempt_id)

            # If this attempt was already fully evaluated, do nothing.
            # This prevents double-processing if the student submitted normally
            # and the beacon also fires (both can happen).
            if attempt.ai_evaluated:
                return Response(
                    {'message': 'Attempt already evaluated. No action taken.'},
                    status=status.HTTP_200_OK
                )

            # Evaluate only MCQ answers that are already saved in the database.
            # Unanswered questions will correctly show 0 points.
            evaluate_mcq_orm(attempt_id)

            # Sum up all points_earned from saved answers (MCQ only at this stage).
            total = StudentAnswers.objects.filter(
                attemptid=attempt_id
            ).aggregate(
                total_earned=Sum('points_earned')
            ).get('total_earned') or Decimal(0)

            # Save the total score to the attempt record.
            attempt.total_score = total
            attempt.updated_at = timezone.now()
            attempt.save()

            # Run the stored procedure to create/update the exam_results record.
            with connection.cursor() as cursor:
                cursor.execute("EXEC sp_calculate_exam_results @attemptId = %s", [attempt_id])

            return Response({
                'message': 'Exam force-completed and MCQ results saved successfully.',
                'attempt_id': attempt_id,
                'total_score': float(total)
            }, status=status.HTTP_200_OK)

        except ExamAttempts.DoesNotExist:
            return Response(
                {'error': f'Attempt ID {attempt_id} not found.'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            import traceback
            print(f"ForceCompleteExamView Error: {traceback.format_exc()}")
            return Response(
                {'error': 'Force complete failed.', 'detail': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

# ─── ADD THIS CLASS AT THE END OF views.py ────────────────────────────────────

class GenerateQuestionsView(APIView):
    """
    POST /exams/generate-questions/
    Uses OpenAI to generate exam questions based on a topic, type, and count.

    Request body:
    {
        "subject":       "Python Programming",
        "topic":         "List comprehensions and lambda functions",
        "question_type": "mcq" | "descriptive" | "coding",
        "count":         5
    }

    Response: { "questions": [ ... ] }
    """
    permission_classes = [AllowAny]

    def post(self, request):
        subject       = request.data.get("subject", "General")
        topic         = request.data.get("topic", "")
        question_type = request.data.get("question_type", "mcq")
        count         = int(request.data.get("count", 5))

        if not topic.strip():
            return Response(
                {"error": "topic is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        count = max(1, min(count, 15))  # clamp between 1 and 15

        # ── Build type-specific prompt ────────────────────────────────────────
        if question_type == "mcq":
            format_instructions = """
For each question return a JSON object with:
  - "questionText": string
  - "questionType": "mcq"
  - "points": integer (between 1 and 5)
  - "options": array of exactly 4 strings (option texts)
  - "correctOption": integer index (0–3) of the correct option
"""
        elif question_type == "descriptive":
            format_instructions = """
For each question return a JSON object with:
  - "questionText": string (open-ended, thought-provoking)
  - "questionType": "discriptive"
  - "points": integer (between 5 and 10)
  - "options": []
"""
        else:  # coding
            format_instructions = """
For each question return a JSON object with:
  - "questionText": string (a clear coding problem/challenge)
  - "questionType": "coding"
  - "points": integer (between 5 and 15)
  - "options": []
"""

        prompt = f"""
You are an expert exam question creator for professional technical assessments.

Subject: {subject}
Topic: {topic}
Question Type: {question_type}
Number of Questions: {count}

Generate exactly {count} high-quality exam questions.
{format_instructions}

Return ONLY a valid JSON array of question objects — no markdown, no explanation, no preamble.
Example structure for the array:
[
  {{ "questionText": "...", "questionType": "...", "points": 2, "options": [...], "correctOption": 1 }}
]
"""

        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
            )

            raw = response.choices[0].message.content.strip()

            # Strip any accidental markdown fences
            if raw.startswith("```"):
                raw = raw.split("```")[1]
                if raw.startswith("json"):
                    raw = raw[4:]

            import json
            questions = json.loads(raw)

            # Sanitise: ensure options array always exists
            for q in questions:
                if "options" not in q:
                    q["options"] = []
                if q.get("questionType") != "mcq":
                    q["options"] = []
                    q.pop("correctOption", None)
                elif "correctOption" not in q:
                    q["correctOption"] = 0

            return Response({"questions": questions}, status=status.HTTP_200_OK)

        except json.JSONDecodeError as e:
            return Response(
                {"error": "AI returned malformed JSON.", "detail": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        except Exception as e:
            import traceback
            print(f"GenerateQuestionsView Error: {traceback.format_exc()}")
            return Response(
                {"error": "Question generation failed.", "detail": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )