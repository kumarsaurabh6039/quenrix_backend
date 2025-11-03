# batches/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.db import connection
from .serializers import AssignUserToBatchSerializer, BatchCreateSerializer

class BatchCreateView(APIView):
    def post(self, request):
        serializer = BatchCreateSerializer(data=request.data)
        if serializer.is_valid():
            batch_name = serializer.validated_data['batchName']
            course_id = serializer.validated_data['courseId']

            try:
                with connection.cursor() as cursor:
                    cursor.execute("""
                        EXEC sp_create_batch_from_course
                            @batchName = %s,
                            @courseId = %s
                    """, [batch_name, course_id])

                    columns = [col[0] for col in cursor.description]
                    row = cursor.fetchone()
                    result = dict(zip(columns, row)) if row else {}

                return Response(result, status=status.HTTP_201_CREATED)

            except Exception as e:
                return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



class BatchesByCourseView(APIView):
    def get(self, request, course_id):
        try:
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT batchId, batchName, is_active
                    FROM batches
                    WHERE courseId = %s
                """, [course_id])
                columns = [col[0] for col in cursor.description]
                rows = cursor.fetchall()
                result = [dict(zip(columns, row)) for row in rows]

            return Response(result, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class AssignUserToBatchView(APIView):
    def post(self, request):
        serializer = AssignUserToBatchSerializer(data=request.data)
        if serializer.is_valid():
            batch_id = serializer.validated_data['batchId']
            user_id = serializer.validated_data['userId']
            role = serializer.validated_data['role']

            try:
                with connection.cursor() as cursor:
                    if role == 'trainer':
                        cursor.execute("""
                            INSERT INTO trainer_batches (batchId, userId)
                            VALUES (%s, %s)
                        """, [batch_id, user_id])
                    else:
                        cursor.execute("""
                            INSERT INTO student_batches (batchId, userId)
                            VALUES (%s, %s)
                        """, [batch_id, user_id])

                return Response({'detail': f'{role.capitalize()} assigned to batch.'}, status=status.HTTP_200_OK)

            except Exception as e:
                return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class DeactivateBatchView(APIView):
    def patch(self, request, batch_id):
        try:
            with connection.cursor() as cursor:
                cursor.execute("""
                    UPDATE batches SET is_active = 0 WHERE batchId = %s
                """, [batch_id])
            return Response({'detail': f'Batch {batch_id} deactivated.'}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class ReactivateBatchView(APIView):
    def patch(self, request, batch_id):
        try:
            with connection.cursor() as cursor:
                cursor.execute("""
                    UPDATE batches SET is_active = 1 WHERE batchId = %s
                """, [batch_id])
            return Response({'detail': f'Batch {batch_id} reactivated.'}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)



from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.db import connection


class BatchUsersView(APIView):
    """
    Get all users (students + trainers) assigned to a batch,
    including their role name from the Roles table.
    """
    def get(self, request, batch_id):
        try:
            with connection.cursor() as cursor:
                # 🧑‍🏫 Trainers
                cursor.execute("""
                    SELECT 
                        u.userId, 
                        u.username, 
                        r.roleName
                    FROM trainer_batches tb
                    INNER JOIN users u ON u.userId = tb.userId
                    LEFT JOIN roles r ON u.roleId = r.roleId
                    WHERE tb.batchId = %s
                """, [batch_id])
                trainer_columns = [col[0] for col in cursor.description]
                trainers = [dict(zip(trainer_columns, row)) for row in cursor.fetchall()]

                # 🧑‍🎓 Students
                cursor.execute("""
                    SELECT 
                        u.userId, 
                        u.username, 
                        r.roleName
                    FROM student_batches sb
                    INNER JOIN users u ON u.userId = sb.userId
                    LEFT JOIN roles r ON u.roleId = r.roleId
                    WHERE sb.batchId = %s
                """, [batch_id])
                student_columns = [col[0] for col in cursor.description]
                students = [dict(zip(student_columns, row)) for row in cursor.fetchall()]

            # ✅ Combine results
            result = {
                "batchId": batch_id,
                "trainers": trainers,
                "students": students
            }

            return Response(result, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
