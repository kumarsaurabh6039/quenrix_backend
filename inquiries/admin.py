from django.contrib import admin

from inquiries.models import CourseInquiry

class CourseInquiryAdmin(admin.ModelAdmin):
    list_display = ('name', 'course_name', 'phone_number', 'email', 'created_at')
    search_fields = ('name', 'phone_number', 'email')
    list_filter = ('course_name', 'created_at')

admin.site.register(CourseInquiry, CourseInquiryAdmin)
