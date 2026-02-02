from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.db import connection
from rest_framework.permissions import AllowAny
from zoom.services import create_recurring_meeting
from .serializers import AssignUserToBatchSerializer, BatchCreateSerializer

class TrainerBatchesView(APIView):
    """
    API view to fetch all batches assigned to a specific trainer.
    Includes Zoom links, schedules, and batch metadata for dashboard integration.
    """
    permission_classes = [AllowAny]

    def get(self, request, user_id):
        try:
            with connection.cursor() as cursor:
                # Join trainer_batches with batches table to retrieve comprehensive data
                cursor.execute("""
                    SELECT 
                        tb.trainerBatchId as trainerbatchid, 
                        tb.batchId as batchid, 
                        tb.userId as userid, 
                        b.batchName as batch_name, 
                        b.courseId as course_id,
                        b.startDate as start_date,
                        b.timing as timing,
                        b.mode as mode,
                        b.zoom_join_url as zoom_join_url
                    FROM trainer_batches tb
                    INNER JOIN batches b ON tb.batchId = b.batchId
                    WHERE tb.userId = %s AND b.is_active = 1
                """, [user_id])
                
                if cursor.description:
                    columns = [col[0] for col in cursor.description]
                    rows = cursor.fetchall()
                    result = [dict(zip(columns, row)) for row in rows]
                else:
                    result = []
            return Response(result, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)

class BatchCreateView(APIView):
    """
    Handles batch creation and automatically generates an associated Zoom meeting.
    """
    def post(self, request):
        serializer = BatchCreateSerializer(data=request.data)
        if serializer.is_valid():
            batch_name = serializer.validated_data['batchName']
            course_id = serializer.validated_data['courseId']
            start_date = serializer.validated_data['start_date']
            timing = serializer.validated_data['timing']
            mode = serializer.validated_data['mode']

            try:
                # 1. Generate Zoom Meeting details using the internal service
                zoom = create_recurring_meeting(batch_name)

                if "id" not in zoom:
                    return Response({"detail": "Zoom meeting creation failed"}, status=status.HTTP_400_BAD_REQUEST)

                zoom_id = zoom["id"]
                zoom_url = zoom["join_url"]

                # 2. Execute Stored Procedure for database persistence in SQL Server
                with connection.cursor() as cursor:
                    cursor.execute("""
                        EXEC sp_create_batch_from_course
                            @batchName = %s,
                            @courseId = %s,
                            @startDate = %s,
                            @timing = %s,
                            @mode = %s,
                            @zoomMeetingId = %s,
                            @zoomJoinUrl = %s
                    """, [batch_name, course_id, start_date, timing, mode, zoom_id, zoom_url])
                    
                    new_batch_id = None
                    if cursor.description:
                        row = cursor.fetchone()
                        if row: 
                            new_batch_id = row[0]

                return Response({
                    "batchId": new_batch_id,
                    "batchName": batch_name,
                    "zoomLink": zoom_url,
                    "message": "Batch created successfully."
                }, status=status.HTTP_201_CREATED)

            except Exception as e:
                return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class BatchesByCourseView(APIView):
    """
    Retrieves all batches associated with a specific course ID.
    """
    permission_classes = [AllowAny]
    def get(self, request, course_id):
        try:
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT batchId, batchName, is_active, startDate, timing, mode, zoom_join_url 
                    FROM batches 
                    WHERE courseId = %s
                """, [course_id])
                
                if cursor.description:
                    columns = [col[0] for col in cursor.description]
                    result = [dict(zip(columns, row)) for row in cursor.fetchall()]
                else:
                    result = []
            return Response(result, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)

class AssignUserToBatchView(APIView):
    """
    Assigns a student or trainer to a specific batch.
    """
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
                return Response({'detail': 'User assignment successful.'}, status=status.HTTP_200_OK)
            except Exception as e:
                return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class DeactivateBatchView(APIView):
    """
    Sets the active status of a batch to false.
    """
    def patch(self, request, batch_id):
        try:
            with connection.cursor() as cursor:
                cursor.execute("UPDATE batches SET is_active = 0 WHERE batchId = %s", [batch_id])
            return Response({'detail': 'Batch deactivated successfully.'}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)

class ReactivateBatchView(APIView):
    """
    Sets the active status of a batch back to true.
    """
    def patch(self, request, batch_id):
        try:
            with connection.cursor() as cursor:
                cursor.execute("UPDATE batches SET is_active = 1 WHERE batchId = %s", [batch_id])
            return Response({'detail': 'Batch reactivated successfully.'}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)

class BatchUsersView(APIView):
    """
    Fetches lists of all trainers and students enrolled in a specific batch.
    """
    def get(self, request, batch_id):
        try:
            with connection.cursor() as cursor:
                # Fetching Trainers
                cursor.execute("""
                    SELECT u.userId, u.username, r.roleName
                    FROM trainer_batches tb
                    INNER JOIN users u ON u.userId = tb.userId
                    LEFT JOIN roles r ON u.roleId = r.roleId
                    WHERE tb.batchId = %s
                """, [batch_id])
                t_cols = [col[0] for col in cursor.description]
                trainers = [dict(zip(t_cols, row)) for row in cursor.fetchall()]

                # Fetching Students
                cursor.execute("""
                    SELECT u.userId, u.username, r.roleName
                    FROM student_batches sb
                    INNER JOIN users u ON u.userId = sb.userId
                    LEFT JOIN roles r ON u.roleId = r.roleId
                    WHERE sb.batchId = %s
                """, [batch_id])
                s_cols = [col[0] for col in cursor.description]
                students = [dict(zip(s_cols, row)) for row in cursor.fetchall()]

            return Response({
                "batchId": batch_id, 
                "trainers": trainers, 
                "students": students
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)