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

    """
    Info around the below helper methods :-
     - The logic is going to be :-
     - Getting the last request, taking all of the messages, inserting the last
       response to that, and then creating a new array (i.e list) of messages that
       we can send for the next request.

    """

    def get_last_request(self):
        """Return the most recent OpenAiRequest or None"""
        return self.openairequest_set.all().order_by('-created_at').first()

    def _create_message(self, message, role="user"):
        """Create a message for the AI."""
        return {"role": role, "content": message}

    def create_first_message(self, message):
        """Create the first message in the session."""
        return [
            self._create_message(
                "You are a snarky and unhelpful assistant.",
                "system"
            ),
            self._create_message(message, "user")
        ]

    def messages(self):
        """Return messages in the conversation including the AI response."""
        all_messages = []
        request = self.get_last_request()

        if request:
            all_messages.extend(request.messages)
            try:
                all_messages.append(request.response["choices"][0]["message"])
            except (KeyError, TypeError, IndexError):
                pass

        return all_messages

    def send(self, message):
        """Send a message to the AI."""
        last_request = self.get_last_request()

        if not last_request:
            OpenAiRequest.objects.create(
                session=self, messages=self.create_first_message(message))
        elif last_request.status in [OpenAiRequest.COMPLETE, OpenAiRequest.FAILED]:
            OpenAiRequest.objects.create(
                session=self,
                messages=self.messages() + [
                    self._create_message(message, "user")
                ]
            )
        else:
            return

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