from django.contrib import admin
from .models import SuccessStory

@admin.register(SuccessStory)
class SuccessStoryAdmin(admin.ModelAdmin):
    # Admin panel mein columns dikhane ke liye
    list_display = ('name', 'company', 'role', 'package', 'created_at')
    # Search functionality
    search_fields = ('name', 'company', 'role')
    # Filter by company
    list_filter = ('company', 'created_at')