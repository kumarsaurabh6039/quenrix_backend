from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import JobApplication
from .serializers import JobApplicationSerializer
# Reusing the AWS utility from blogs app exactly like notes app
from blogs.utils.aws import generate_presigned_url
import uuid

# Same bucket as used in notes app
BUCKET = "amzn-hyd-myapp-lms-bucket01"

@api_view(["POST"])
def submit_application(request):
    try:
        data = request.data
        
        # 1. Basic Validation
        full_name = data.get("fullName")
        job_id = data.get("jobId")
        
        if not full_name or not job_id:
            return Response({"error": "Full Name and Job ID are required"}, status=400)

        # 2. Generate S3 Path for Resume
        # Path format: Resumes/Job_<ID>/<UUID>.pdf
        filename = f"{uuid.uuid4()}.pdf" # Assuming PDF, can be dynamic based on extension
        object_key = f"Resumes/Job_{job_id}/{filename}"

        # 3. Generate Presigned URL (Direct Upload Link)
        presigned_url = generate_presigned_url(BUCKET, object_key)

        if not presigned_url:
            return Response({"error": "Failed to generate S3 URL"}, status=500)

        # 4. Construct the Final Public URL for DB
        s3_file_url = f"https://{BUCKET}.s3.ap-south-2.amazonaws.com/{object_key}"

        # 5. Create Database Entry
        # Mapping frontend camelCase to backend snake_case
        application = JobApplication.objects.create(
            job_id=job_id,
            full_name=full_name,
            email=data.get("email"),
            phone=data.get("phone"),
            dob=data.get("dob"),
            gender=data.get("gender"),
            location=data.get("location"),
            
            degree=data.get("degree"),
            university=data.get("university"),
            grad_year=data.get("gradYear"),
            cgpa=data.get("cgpa"),
            
            work_status=data.get("workStatus", "Fresher"),
            current_company=data.get("currentCompany"),
            job_title=data.get("jobTitle"),
            experience_years=data.get("experienceYears"),
            current_ctc=data.get("currentCTC"),
            expected_ctc=data.get("expectedCTC"),
            notice_period=data.get("noticePeriod"),
            
            linkedin_url=data.get("linkedin"),
            portfolio_url=data.get("portfolio"),
            
            resume_url=s3_file_url # Saving the S3 path
        )

       
        return Response({
            "message": "Application created successfully",
            "upload_url": presigned_url,  # Frontend uses this to upload file
            "application_id": application.id
        })

    except Exception as e:
        print(f"Error submitting application: {e}")
        return Response({"error": str(e)}, status=500)