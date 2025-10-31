from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.db import connection
from .models import Createjob
from .serializers import CreateJobSerializer, CreateJobRequestSerializer


@api_view(['GET'])
def list_jobs(request):
    """List all jobs"""
    jobs = Createjob.objects.all().order_by('-posteddate')
    serializer = CreateJobSerializer(jobs, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['POST'])
def create_job(request):
    """Create job via stored procedure"""
    serializer = CreateJobRequestSerializer(data=request.data)
    if serializer.is_valid():
        data = serializer.validated_data
        with connection.cursor() as cursor:
            cursor.execute("""
                EXEC sp_create_job 
                    @p_jobtitle=%s,
                    @p_job_type=%s,
                    @p_reqexp=%s,
                    @p_company=%s,
                    @p_location=%s,
                    @p_from_passed_out_year=%s,
                    @p_to_passed_out_year=%s,
                    @p_hr_phone=%s,
                    @p_hr_email=%s,
                    @p_job_description=%s,
                    @p_apply_before_date=%s,
                    @p_is_active=%s
            """, [
                data['jobtitle'],
                data['job_type'],
                data['reqexp'],
                data['company'],
                data['location'],
                data['from_passed_out_year'],
                data['to_passed_out_year'],
                data['hr_phone'],
                data['hr_email'],
                data['job_description'],
                data['apply_before_date'],
                data['is_active'],
            ])
            row = cursor.fetchone()

        return Response({
            "message": "Job created successfully",
            "jobId": row[1] if row else None
        }, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
