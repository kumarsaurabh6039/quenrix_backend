from django.urls import path
from .views import (
    CalculateExamResultView, EvaluateAIDescriptiveCodingView, EvaluateCompleteExamView, EvaluateMCQAnswersView, ExamCreateView, ExamListView, ExamDetailView, QuestionListView,
    ExamAttemptCreateView, StudentAnswerCreateView, ExamResultListView, StudentExamAttemptListView, StudentExamListView, StudentFinalResultView,
    StudentBatchByUserIdView
)

urlpatterns = [
    path('exam-list/', ExamListView.as_view(), name='exam-list'),
    path('exam-details/<int:examid>/', ExamDetailView.as_view(), name='exam-details'),
    path('exam-questions/<int:examid>/', QuestionListView.as_view(), name='exam-questions'),
    path('attempt/create/', ExamAttemptCreateView.as_view(), name='exam-attempt-create'),
    path('answer/create/', StudentAnswerCreateView.as_view(), name='student-answer-create'),
    path('results/', ExamResultListView.as_view(), name='exam-results'),
    path('evaluate-mcq/<int:attempt_id>/', EvaluateMCQAnswersView.as_view(), name='evaluate-mcq'),
    path('results/calculate/<int:attempt_id>/', CalculateExamResultView.as_view(), name='calculate-exam-result'),
    path('create-exam/', ExamCreateView.as_view(), name='exam-create'),
    path('student-exams/<int:course_id>/<int:batch_id>/', StudentExamListView.as_view(), name='student-exam-list'),
    path('student-batches/<str:user_id>/', StudentBatchByUserIdView.as_view(), name='student-batches-by-user'),
    path('student-exam-attempts/<str:user_id>/', StudentExamAttemptListView.as_view(), name='student-exam-attempts'),
    path('evaluate-ai/<int:attempt_id>/', EvaluateAIDescriptiveCodingView.as_view(), name='evaluate-ai'),
    path('results/student/<str:user_id>/', StudentFinalResultView.as_view(), name='student-results'),
    path('results/student/<str:user_id>/exam/<int:exam_id>/', StudentFinalResultView.as_view(), name='student-exam-result'),
    path('evaluate-complete/<int:attempt_id>/', EvaluateCompleteExamView.as_view(), name='evaluate-complete'),

]
