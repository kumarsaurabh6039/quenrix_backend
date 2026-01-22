from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import CourseInquiry
from .serializers import CourseInquirySerializer
from rest_framework.permissions import AllowAny
from django.utils.dateparse import parse_date

class InquiryCreateView(APIView):
    permission_classes = [AllowAny]
    
    def post(self, request):
        print("Data received:", request.data) 
        
        email = request.data.get('email')
        course_name = request.data.get('course_name')

        # --- DUPLICATE CHECK ---
        if email and course_name:
            if CourseInquiry.objects.filter(email=email, course_name=course_name).exists():
                return Response(
                    {"message": "We already have your details for this course. The Quenrix team will connect with you shortly."}, 
                    status=status.HTTP_400_BAD_REQUEST
                )

        serializer = CourseInquirySerializer(data=request.data)
        
        if serializer.is_valid():
            serializer.save()
            return Response(
                {"message": "Inquiry submitted successfully!"}, 
                status=status.HTTP_201_CREATED
            )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# API for Fetching
class InquiryListView(APIView):
    def get(self,request):
        inquiries = CourseInquiry.objects.all().order_by('-created_at')
        serializer = CourseInquirySerializer(inquiries, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

# NEW: API for Deleting
class InquiryDeleteView(APIView):
    def delete(self, request):
        # 1. Delete Single by ID
        inquiry_id = request.query_params.get('id')
        if inquiry_id:
            try:
                CourseInquiry.objects.get(id=inquiry_id).delete()
                return Response({"message": "Inquiry deleted successfully"}, status=status.HTTP_200_OK)
            except CourseInquiry.DoesNotExist:
                return Response({"error": "Inquiry not found"}, status=status.HTTP_404_NOT_FOUND)

        # 2. Delete All
        delete_all = request.query_params.get('delete_all')
        if delete_all == 'true':
            CourseInquiry.objects.all().delete()
            return Response({"message": "All inquiries deleted successfully"}, status=status.HTTP_200_OK)
            
        # 3. Delete by Date Range
        start_date_str = request.query_params.get('start_date')
        end_date_str = request.query_params.get('end_date')
        
        if start_date_str and end_date_str:
            start_date = parse_date(start_date_str)
            end_date = parse_date(end_date_str)
            
            if start_date and end_date:
                # Filter by date range (inclusive)
                CourseInquiry.objects.filter(created_at__date__gte=start_date, created_at__date__lte=end_date).delete()
                return Response({"message": f"Inquiries from {start_date} to {end_date} deleted"}, status=status.HTTP_200_OK)

        return Response({"error": "No valid parameters provided"}, status=status.HTTP_400_BAD_REQUEST)