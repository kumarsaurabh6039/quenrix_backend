from django.contrib import admin
from .models import ChatbotCategory, ChatbotDocument, TextChunk


@admin.register(ChatbotCategory)
class ChatbotCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_active', 'created_at')
    list_filter = ('is_active',)
    search_fields = ('name',)


class TextChunkInline(admin.TabularInline):
    model = TextChunk
    fields = ('chunk_index', 'chunk_text')
    readonly_fields = ('chunk_index', 'chunk_text')
    extra = 0
    max_num = 0
    can_delete = False


@admin.register(ChatbotDocument)
class ChatbotDocumentAdmin(admin.ModelAdmin):
    list_display = ('file_name', 'category', 'file_type', 'is_processed', 'chunk_count', 'uploaded_at')
    list_filter = ('category', 'file_type', 'is_processed')
    search_fields = ('file_name',)
    readonly_fields = ('s3_url', 'chunk_count', 'uploaded_at')
    inlines = [TextChunkInline]
