from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import CourseInquiry
from .serializers import CourseInquirySerializer
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView
from rest_framework.response import Response
class InquiryCreateView(APIView):
    permission_classes = [AllowAny]
    def post(self, request):
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