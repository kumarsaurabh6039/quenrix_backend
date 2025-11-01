# resume/views.py
from django.db import connection
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from resume.models import ProficiencyLevels, SkillCategories, SkillsMaster, TechStack
from .serializers import ProficiencyLevelSerializer, ResumeSerializer, ResumeResponseSerializer, SkillCategorySerializer, SkillsMasterSerializer, TechStackSerializer
import json

from rest_framework.decorators import api_view

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
        

class ResumeSetupDataView(APIView):
    """
    Fetches all tech stacks, skills, and proficiency levels
    to display on resume creation form
    """
    def get(self, request):
        try:
            tech_stacks = TechStack.objects.all()
            skills = SkillsMaster.objects.all()
            proficiencies = ProficiencyLevels.objects.all()

            tech_stack_data = TechStackSerializer(tech_stacks, many=True).data
            skill_data = SkillsMasterSerializer(skills, many=True).data
            proficiency_data = ProficiencyLevelSerializer(proficiencies, many=True).data

            return Response({
                "techStacks": tech_stack_data,
                "skills": skill_data,
                "proficiencies": proficiency_data
            }, status=200)
        except Exception as e:
            return Response({"error": str(e)}, status=400)
        

class AddTechStackView(APIView):
    def post(self, request):
        serializer = TechStackSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Tech Stack added successfully", "data": serializer.data}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AddSkillView(APIView):
    def post(self, request):
        serializer = SkillsMasterSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Skill added successfully", "data": serializer.data}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AddProficiencyView(APIView):
    def post(self, request):
        serializer = ProficiencyLevelSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Proficiency Level added successfully", "data": serializer.data}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    

# ✅ Fetch all categories
@api_view(['GET'])
def get_skill_categories(request):
    categories = SkillCategories.objects.all()
    serializer = SkillCategorySerializer(categories, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)

# ✅ Add a new category
@api_view(['POST'])
def add_skill_category(request):
    serializer = SkillCategorySerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)