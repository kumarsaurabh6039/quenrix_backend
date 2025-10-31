from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.db import connection
from .models import Doubts, Solutions
from .serializers import (
    DoubtsSerializer, CreateDoubtSerializer,
    SolutionsSerializer, CreateSolutionSerializer
)


class CreateDoubtView(APIView):
    def post(self, request):
        serializer = CreateDoubtSerializer(data=request.data)
        if serializer.is_valid():
            subjectid = serializer.validated_data['subjectid']
            userid = serializer.validated_data['userid']
            doubttext = serializer.validated_data['doubttext']

            try:
                with connection.cursor() as cursor:
                    cursor.execute("""
                        EXEC sp_create_doubt @subjectId=%s, @userId=%s, @doubtText=%s
                    """, [subjectid, userid, doubttext])
                    result = cursor.fetchall()
                    if result:
                        columns = [col[0] for col in cursor.description]
                        data = [dict(zip(columns, row)) for row in result]
                        return Response(data[0], status=status.HTTP_201_CREATED)
                    return Response({"message": "No data returned."}, status=status.HTTP_200_OK)
            except Exception as e:
                return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CreateSolutionView(APIView):
    def post(self, request):
        serializer = CreateSolutionSerializer(data=request.data)
        if serializer.is_valid():
            doubtid = serializer.validated_data['doubtid']
            solution = serializer.validated_data['solution']
            userid = serializer.validated_data.get('userid', None)

            try:
                with connection.cursor() as cursor:
                    cursor.execute("""
                        EXEC sp_create_solution @doubtId=%s, @solution=%s, @userId=%s
                    """, [doubtid, solution, userid])
                    result = cursor.fetchall()
                    if result:
                        columns = [col[0] for col in cursor.description]
                        data = [dict(zip(columns, row)) for row in result]
                        return Response(data[0], status=status.HTTP_201_CREATED)
                    return Response({"message": "No data returned."}, status=status.HTTP_200_OK)
            except Exception as e:
                return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ListDoubtsView(APIView):
    def get(self, request):
        doubts = Doubts.objects.filter(is_active=True)
        serializer = DoubtsSerializer(doubts, many=True)
        return Response(serializer.data)


class ListSolutionsView(APIView):
    def get(self, request):
        solutions = Solutions.objects.filter(is_active=True)
        serializer = SolutionsSerializer(solutions, many=True)
        return Response(serializer.data)
