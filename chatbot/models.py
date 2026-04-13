from django.db import models


class ChatbotCategory(models.Model):
    """
    Topic categories for the chatbot (e.g., "About Quenrix", "Policies", "Placement").
    Admin creates these; users select one before chatting.
    """
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, default='')
    icon = models.CharField(max_length=50, default='fas fa-folder')  # FontAwesome class
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "Chatbot Categories"
        ordering = ['name']

    def __str__(self):
        return self.name


class ChatbotDocument(models.Model):
    """
    PDF / image documents uploaded by admin, linked to a category.
    Text is extracted and chunked for RAG retrieval.
    """
    FILE_TYPE_CHOICES = [
        ('pdf', 'PDF'),
        ('image', 'Image'),
        ('text', 'Plain Text'),
    ]

    category = models.ForeignKey(
        ChatbotCategory,
        on_delete=models.CASCADE,
        related_name='documents'
    )
    file_name = models.CharField(max_length=255)
    file_type = models.CharField(max_length=10, choices=FILE_TYPE_CHOICES)
    s3_key = models.CharField(max_length=500)
    s3_url = models.URLField(max_length=1000)
    is_processed = models.BooleanField(default=False)
    chunk_count = models.IntegerField(default=0)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-uploaded_at']

    def __str__(self):
        return f"{self.file_name} → {self.category.name}"


class TextChunk(models.Model):
    """
    Individual text chunks from a document, each with an OpenAI embedding for similarity search.
    """
    document = models.ForeignKey(
        ChatbotDocument,
        on_delete=models.CASCADE,
        related_name='chunks'
    )
    chunk_text = models.TextField()
    chunk_index = models.IntegerField()
    # Stored as a JSON list of floats (OpenAI ada-002 → 1536 dims, text-embedding-3-small → 1536 dims)
    embedding = models.JSONField(null=True, blank=True)

    class Meta:
        ordering = ['document', 'chunk_index']

    def __str__(self):
        return f"Chunk {self.chunk_index} | {self.document.file_name}"
