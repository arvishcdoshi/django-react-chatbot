from celery import shared_task

from core import models

@shared_task
def hello_task(name):
    print(f"Hello {name}. You have {len(name)} characters in your name.")


@shared_task
def handle_openai_request_job(openai_request_id):
    models.OpenAiRequest.objects.get(id=openai_request_id).handle()
