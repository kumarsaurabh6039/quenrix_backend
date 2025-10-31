from django.urls import path
from .views import (
    CalculateExamResultView, EvaluateMCQAnswersView, ExamCreateView, ExamListView, ExamDetailView, QuestionListView,
    ExamAttemptCreateView, StudentAnswerCreateView, ExamResultListView
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
    path('exam/create/', ExamCreateView.as_view(), name='exam-create'),

]
