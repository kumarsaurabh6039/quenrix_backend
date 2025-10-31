from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.db import connection
from .models import SubjectsTopicswiseQuestions
from .serializers import (
    SubjectsTopicswiseQuestionsSerializer,
    CreateTopicwiseQuestionRequestSerializer
)


@api_view(['GET'])
def list_topicwise_questions(request):
    """List all topicwise questions"""
    topics = SubjectsTopicswiseQuestions.objects.select_related('subjectid').order_by('-created_at')
    serializer = SubjectsTopicswiseQuestionsSerializer(topics, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['POST'])
def create_topicwise_question(request):
    """Create topic via stored procedure"""
    serializer = CreateTopicwiseQuestionRequestSerializer(data=request.data)
    if serializer.is_valid():
        data = serializer.validated_data
        try:
            with connection.cursor() as cursor:
                cursor.execute("""
                    EXEC sp_create_topicwise_questions 
                        @subjectId=%s,
                        @topicName=%s,
                        @practice_questions_url=%s
                """, [
                    data['subjectId'],
                    data['topicName'],
                    data.get('practice_questions_url', None),
                ])
                row = cursor.fetchone()

            # Map result properly if returned
            if row:
                response_data = {
                    "topicId": row[0],
                    "subjectId": row[1],
                    "topicName": row[2],
                    "practice_questions_url": row[3],
                    "created_at": row[4],
                    "message": row[5]
                }
            else:
                response_data = {"message": "Topicwise questions created successfully"}

            return Response(response_data, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
