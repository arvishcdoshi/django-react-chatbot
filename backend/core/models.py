from django.db import models


class Recipe(models.Model):
    """Represents a recipe in the system."""
    name = models.CharField(max_length=255)
    steps = models.TextField()

    def __str__(self):
        return self.name


class OpenAiChatSession(models.Model):
    """Tracks an AI chat session."""
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class OpenAiRequest(models.Model):
    """Represents an AI request."""

    PENDING = 'pending'
    RUNNING = 'running'
    COMPLETE = 'complete'
    FAILED = 'failed'
    STATUS_OPTIONS = (
        (PENDING, 'Pending'),
        (RUNNING, 'Running'),
        (COMPLETE, 'Complete'),
        (FAILED, 'Failed')
    )

    status = models.CharField(choices=STATUS_OPTIONS, default=PENDING)
    session = models.ForeignKey(
        OpenAiChatSession,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )
    messages = models.JSONField()
    response = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)