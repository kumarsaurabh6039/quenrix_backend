# resume/views.py
from django.db import connection
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import ResumeSerializer, ResumeResponseSerializer
import json


class CreateOrUpdateResumeView(APIView):
    """
    Calls stored procedure: sp_create_resume
    """

    def post(self, request):
        serializer = ResumeSerializer(data=request.data)
        if serializer.is_valid():
            data = serializer.validated_data
            try:
                with connection.cursor() as cursor:
                    cursor.execute("""
                        EXEC sp_create_resume 
                            @userId=%s,
                            @personalInfo=%s,
                            @education=%s,
                            @experience=%s,
                            @skills=%s,
                            @projects=%s
                    """, [
                        data.get("userId"),
                        json.dumps(data.get("personalInfo")) if data.get("personalInfo") else None,
                        json.dumps(data.get("education")) if data.get("education") else None,
                        json.dumps(data.get("experience")) if data.get("experience") else None,
                        json.dumps(data.get("skills")) if data.get("skills") else None,
                        json.dumps(data.get("projects")) if data.get("projects") else None,
                    ])
                    result = cursor.fetchall()
                return Response({"message": "✅ Resume created/updated successfully"}, status=status.HTTP_200_OK)
            except Exception as e:
                return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class GetResumeView(APIView):
    """
    Calls stored procedure: sp_get_resume
    """

    def get(self, request, userId):
        try:
            with connection.cursor() as cursor:
                cursor.execute("EXEC sp_get_resume @userId=%s", [userId])
                result = cursor.fetchone()

                if result and result[0]:
                    resume_data = json.loads(result[0])

                    # ✅ Parse nested JSON strings safely
                    for field in ["education", "experience", "skills", "projects"]:
                        if field in resume_data and isinstance(resume_data[field], str):
                            try:
                                resume_data[field] = json.loads(resume_data[field])
                            except json.JSONDecodeError:
                                resume_data[field] = []

                    return Response(resume_data, status=status.HTTP_200_OK)

                else:
                    return Response(
                        {"message": "No resume found for given userId"},
                        status=status.HTTP_404_NOT_FOUND,
                    )

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)