from openai import OpenAI
from django.db import models
from core.tasks import handle_openai_request_job

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

    def _queue_job(self):
        """Add job to the queue"""
        handle_openai_request_job.delay(self.id)

    def handle(self):
        """Handle request."""
        self.status = self.RUNNING
        self.save()
        client = OpenAI()
        print('CLIENT - ', client)
        try:
            completion = client.chat.completions.create(
                model="gpt-4o-mini",
                messages = self.messages,
            )
            self.response = completion.to_dict()
            self.status = self.COMPLETE
        except Exception as e:
            print('ERROR - ', e)
            self.status = self.FAILED

        self.save()

    def save(self, **kwargs):
        """Trigger the celery job everytime an instance of this model is created - by overriding the save method"""
        is_new = self._state.adding
        super().save(**kwargs)
        if is_new:
            self._queue_job()