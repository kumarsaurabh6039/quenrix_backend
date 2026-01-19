from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAdminUser
from .models import JobApplication
from .serializers import JobApplicationSerializer
from blogs.utils.aws import generate_presigned_url
from django.core.mail import send_mail
from django.conf import settings
import uuid

BUCKET = "amzn-hyd-myapp-lms-bucket01"

# --- EXISTING SUBMIT VIEW ---
@api_view(["POST"])
@permission_classes([AllowAny])          
def submit_application(request):
    try:
        data = request.data
        full_name = data.get("fullName")
        job_id = data.get("jobId")
        email = data.get("email")
        
        if not full_name or not job_id:
            return Response({"error": "Full Name and Job ID are required"}, status=400)

        # Duplicate Check
        if JobApplication.objects.filter(job_id=job_id, email=email).exists():
            return Response(
                {"error": "You have already applied for this position with this email address."}, 
                status=400
            )

        filename = f"{uuid.uuid4()}.pdf"
        object_key = f"Resumes/Job_{job_id}/{filename}"

        presigned_url = generate_presigned_url(BUCKET, object_key)

        if not presigned_url:
            return Response({"error": "Failed to generate S3 URL"}, status=500)

        s3_file_url = f"https://{BUCKET}.s3.ap-south-2.amazonaws.com/{object_key}"

        application = JobApplication.objects.create(
            job_id=job_id,
            full_name=full_name,
            email=email,
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
            
            resume_url=s3_file_url 
        )

        try:
            subject = f"Application Received - Welcome to Quenrix (Job ID: {job_id})"
            message = f"""Dear {full_name},

Welcome to Quenrix!

We have successfully received your job application for the position (ID: {job_id}). 
Our recruitment team will review your profile, and we will contact you shortly if your qualifications match our requirements.

Thank you for your interest in joining us.

Best Regards,
HR Team, Quenrix
"""
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [email],
                fail_silently=True
            )
        except Exception as mail_error:
            print(f"Error sending confirmation email: {mail_error}")

        return Response({
            "message": "Application created successfully",
            "upload_url": presigned_url,  
            "application_id": application.id
        })

    except Exception as e:
        print(f"Error submitting application: {e}")
        return Response({"error": str(e)}, status=500)

# --- NEW: List All Applicants View ---
@api_view(["GET"])
@permission_classes([AllowAny]) # In production, change to [IsAdminUser] or [IsAuthenticated]
def list_applications(request):
    try:
        # Fetch all applications, ordered by latest first
        applications = JobApplication.objects.all().order_by('-applied_at')
        serializer = JobApplicationSerializer(applications, many=True)
        return Response(serializer.data)
    except Exception as e:
        print(f"Error fetching applications: {e}")
        return Response({"error": str(e)}, status=500)