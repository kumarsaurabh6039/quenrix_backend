from django.contrib import admin
from .models import JobApplication

@admin.register(JobApplication)
class JobApplicationAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'job_id', 'work_status', 'email', 'applied_at')
    list_filter = ('work_status', 'degree', 'applied_at')
    search_fields = ('full_name', 'email', 'phone')
    ordering = ('-applied_at',)