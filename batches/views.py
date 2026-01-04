from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.db import connection
from .serializers import AssignUserToBatchSerializer, BatchCreateSerializer
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView
from rest_framework.response import Response
class BatchCreateView(APIView):
    def post(self, request):
        serializer = BatchCreateSerializer(data=request.data)
        if serializer.is_valid():
            
            batch_name = serializer.validated_data['batchName']
            course_id = serializer.validated_data['courseId']
            start_date = serializer.validated_data['start_date']
            timing = serializer.validated_data['timing']
            mode = serializer.validated_data['mode']

            try:
                with connection.cursor() as cursor:
                    cursor.execute("""
                        EXEC sp_create_batch_from_course
                            @batchName = %s,
                            @courseId = %s,
                            @startDate = %s,
                            @timing = %s,
                            @mode = %s
                    """, [batch_name, course_id, start_date, timing, mode])

                    # 3. Batch ID Fetch karo
                    new_batch_id = None
                    if cursor.description:
                        row = cursor.fetchone()
                        if row:
                            # Usually first column is ID
                            new_batch_id = row[0] 

                    # 4. Success Response
                    result = {
                        "batchId": new_batch_id,
                        "batchName": batch_name,
                        "courseId": course_id,
                        "startDate": start_date,
                        "timing": timing,
                        "mode": mode,
                        "message": "Batch created successfully."
                    }

                return Response(result, status=status.HTTP_201_CREATED)

            except Exception as e:
                # Agar SQL se error aaye toh yahan dikhega
                return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)

        # Validation Error
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# --- Baaki Views Same Rahenge ---

class BatchesByCourseView(APIView):
    permission_classes = [AllowAny]
    def get(self, request, course_id):
        try:
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT batchId, batchName, is_active, startDate, timing, mode
                    FROM batches
                    WHERE courseId = %s
                """, [course_id])
                
                if cursor.description:
                    columns = [col[0] for col in cursor.description]
                    rows = cursor.fetchall()
                    result = [dict(zip(columns, row)) for row in rows]
                else:
                    result = []
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
                    table = 'trainer_batches' if role == 'trainer' else 'student_batches'
                    cursor.execute(f"INSERT INTO {table} (batchId, userId) VALUES (%s, %s)", [batch_id, user_id])
                return Response({'detail': f'{role.capitalize()} assigned.'}, status=status.HTTP_200_OK)
            except Exception as e:
                return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class DeactivateBatchView(APIView):
    def patch(self, request, batch_id):
        try:
            with connection.cursor() as cursor:
                cursor.execute("UPDATE batches SET is_active = 0 WHERE batchId = %s", [batch_id])
            return Response({'detail': 'Deactivated'}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)

class ReactivateBatchView(APIView):
    def patch(self, request, batch_id):
        try:
            with connection.cursor() as cursor:
                cursor.execute("UPDATE batches SET is_active = 1 WHERE batchId = %s", [batch_id])
            return Response({'detail': 'Reactivated'}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)

class BatchUsersView(APIView):
    def get(self, request, batch_id):
        try:
            with connection.cursor() as cursor:
                # Trainers
                cursor.execute("""
                    SELECT u.userId, u.username, r.roleName
                    FROM trainer_batches tb
                    INNER JOIN users u ON u.userId = tb.userId
                    LEFT JOIN roles r ON u.roleId = r.roleId
                    WHERE tb.batchId = %s
                """, [batch_id])
                cols = [col[0] for col in cursor.description]
                trainers = [dict(zip(cols, row)) for row in cursor.fetchall()]

                # Students
                cursor.execute("""
                    SELECT u.userId, u.username, r.roleName
                    FROM student_batches sb
                    INNER JOIN users u ON u.userId = sb.userId
                    LEFT JOIN roles r ON u.roleId = r.roleId
                    WHERE sb.batchId = %s
                """, [batch_id])
                cols = [col[0] for col in cursor.description]
                students = [dict(zip(cols, row)) for row in cursor.fetchall()]

            return Response({"batchId": batch_id, "trainers": trainers, "students": students}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)