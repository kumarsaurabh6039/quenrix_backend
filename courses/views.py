from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.db import connection
from .models import Courses, Subjects, SystemSetups
from .serializers import CourseCreateSerializer, CourseSerializer, CourseUpdateSerializer, SubjectSerializer, SystemSetupSerializer
from rest_framework.permissions import AllowAny

class CourseCreateView(APIView):
    def post(self, request):
        serializer = CourseCreateSerializer(data=request.data)
        if serializer.is_valid():
            course_name = serializer.validated_data['courseName']
            content_url = serializer.validated_data['contentUrl']
            subjects_json = serializer.validated_data['subjects']

            # 1. CHECK: Pehle check karein ki Course Name exist karta hai ya nahi
            if Courses.objects.filter(coursename__iexact=course_name).exists():
                return Response(
                    {'detail': f'Course with name "{course_name}" already exists.'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )

            try:
                with connection.cursor() as cursor:
                    cursor.execute("""
                        DECLARE @return_table TABLE (
                            CourseId INT,
                            CourseName NVARCHAR(255),
                            ContentUrl NVARCHAR(500),
                            LinkedSubjects NVARCHAR(MAX),
                            CreatedAt DATETIME
                        );

                        EXEC sp_create_course_with_subjects_and_content
                            @courseName = %s,
                            @contentUrl = %s,
                            @subjects = %s;

                        SELECT * FROM @return_table;
                    """, [course_name, content_url, str(subjects_json).replace("'", '"')])

                    row = cursor.fetchone()
                    if row:
                        result = {
                            'courseId': row[0],
                            'courseName': row[1],
                            'contentUrl': row[2],
                            'linkedSubjects': row[3],
                            'createdAt': row[4]
                        }
                        return Response(result, status=status.HTTP_201_CREATED)
                    else:
                        return Response({'detail': 'Course creation failed via stored procedure.'}, status=status.HTTP_400_BAD_REQUEST)

            except Exception as e:
                # Specific handling for integrity errors if they bypass the first check
                if 'UNIQUE KEY' in str(e) or 'Duplicate entry' in str(e):
                     return Response({'detail': 'Course with this name already exists.'}, status=status.HTTP_400_BAD_REQUEST)
                
                return Response({'detail': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CourseListView(APIView):
    permission_classes = [AllowAny]
    def get(self, request):
        courses = Courses.objects.select_related('contentid').all()
        serializer = CourseSerializer(courses, many=True)
        return Response(serializer.data)


class CourseUpdateView(APIView):
    def put(self, request):
        serializer = CourseUpdateSerializer(data=request.data)
        if serializer.is_valid():
            course_id = serializer.validated_data['courseId']
            course_name = serializer.validated_data.get('courseName')
            content_url = serializer.validated_data.get('contentUrl')
            subjects = serializer.validated_data.get('subjects')

            # 2. CHECK: Update ke time par bhi duplicate name check karein (exclude current course)
            if course_name:
                if Courses.objects.filter(coursename__iexact=course_name).exclude(courseid=course_id).exists():
                    return Response(
                        {'detail': f'Course with name "{course_name}" already exists.'}, 
                        status=status.HTTP_400_BAD_REQUEST
                    )

            try:
                with connection.cursor() as cursor:
                    if course_name:
                        cursor.execute("UPDATE courses SET courseName = %s WHERE courseId = %s", [course_name, course_id])
                    if content_url:
                        cursor.execute("UPDATE content SET contentUrl = %s WHERE contentId = (SELECT contentId FROM courses WHERE courseId = %s)", [content_url, course_id])
                    if subjects is not None: # Check explicitly for None, as empty list is valid
                        cursor.execute("DELETE FROM course_subjects WHERE courseId = %s", [course_id])
                        for subject in subjects:
                            # Using parameterized queries safely
                            cursor.execute("""
                                DECLARE @subjectId INT;
                                SELECT @subjectId = subjectId FROM subjects WHERE LOWER(subjectName) = LOWER(%s);
                                IF @subjectId IS NULL
                                BEGIN
                                    INSERT INTO subjects (subjectName) VALUES (%s);
                                    SET @subjectId = SCOPE_IDENTITY();
                                END
                                INSERT INTO course_subjects (courseId, subjectId) VALUES (%s, @subjectId);
                            """, [subject, subject, course_id])

                    # Fetch updated course details
                    cursor.execute("""
                        SELECT c.courseId, c.courseName, ct.contentUrl
                        FROM courses c
                        JOIN content ct ON c.contentId = ct.contentId
                        WHERE c.courseId = %s
                    """, [course_id])
                    course_row = cursor.fetchone()

                    if not course_row:
                         return Response({'detail': 'Course not found after update.'}, status=status.HTTP_404_NOT_FOUND)

                    cursor.execute("""
                        SELECT s.subjectName
                        FROM subjects s
                        JOIN course_subjects cs ON s.subjectId = cs.subjectId
                        WHERE cs.courseId = %s
                    """, [course_id])
                    subject_rows = cursor.fetchall()

                updated_data = {
                    "courseId": course_row[0],
                    "courseName": course_row[1],
                    "contentUrl": course_row[2],
                    "subjects": [row[0] for row in subject_rows]
                }

                return Response(updated_data, status=status.HTTP_200_OK)

            except Exception as e:
                if 'UNIQUE KEY' in str(e) or 'Duplicate entry' in str(e):
                     return Response({'detail': 'Course with this name already exists.'}, status=status.HTTP_400_BAD_REQUEST)
                return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CourseDeleteView(APIView):
    def delete(self, request, course_id):
        try:
            with connection.cursor() as cursor:
                # Check existence first
                cursor.execute("SELECT Count(*) FROM courses WHERE courseId = %s", [course_id])
                if cursor.fetchone()[0] == 0:
                     return Response({'detail': 'Course not found.'}, status=status.HTTP_404_NOT_FOUND)
                
                cursor.execute("DELETE FROM courses WHERE courseId = %s", [course_id])
            return Response({'detail': f'Course {course_id} deleted.'}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class SubjectWiseSystemSetupView(APIView):
    def get(self, request, subject_id):
        setups = SystemSetups.objects.filter(subjectid=subject_id, is_active=True)
        if not setups.exists():
            return Response(
                {"detail": "No active system setups found for this subject."},
                status=status.HTTP_404_NOT_FOUND
            )
        serializer = SystemSetupSerializer(setups, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
class CourseWiseSubjectsView(APIView):
    """
    Returns all subjects linked to a specific course.
    """
    def get(self, request, course_id):
        try:
            course = Courses.objects.get(pk=course_id)
        except Courses.DoesNotExist:
            return Response(
                {"error": "Course not found."},
                status=status.HTTP_404_NOT_FOUND
            )

        # Get all subjects linked to the course
        subjects = Subjects.objects.filter(
            coursesubjects__courseid=course
        ).distinct()

        serializer = SubjectSerializer(subjects, many=True)
        return Response({
            "course_id": course.courseid,
            "course_name": course.coursename,
            "subjects": serializer.data
        }, status=status.HTTP_200_OK)