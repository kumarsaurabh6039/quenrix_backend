from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import CourseInquiry
from .serializers import CourseInquirySerializer

# 1. Inquiry submit 
class InquiryCreateView(APIView):
    def post(self, request):
        # User manually form fill karega
        print("Data received:", request.data) 
        
        serializer = CourseInquirySerializer(data=request.data)
        
        if serializer.is_valid():
            serializer.save()
            return Response(
                {"message": "Inquiry submitted successfully!"}, 
                status=status.HTTP_201_CREATED
            )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

#api for fetching
class InquiryListView(APIView):
    def get(self,request):
        inquiries = CourseInquiry.objects.all().order_by('-created_at')
        serializer = CourseInquirySerializer(inquiries, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)