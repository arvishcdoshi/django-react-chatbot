from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.shortcuts import get_object_or_404

from core.models import OpenAiChatSession
from core.serializers import OpenAiChatSessionSerializer


@api_view(['POST'])
def create_chat_session(request):
    """ Create a new chat session. """

    session = OpenAiChatSession.objects.create()
    serializer = OpenAiChatSessionSerializer(session)
    return Response(serializer.data, status=status.HTTP_201_CREATED)


@api_view(['GET', 'POST'])
def chat_session(request, session_id):
    """ Retrieve a chat session & its messages. """

    session = get_object_or_404(OpenAiChatSession, id=session_id)
    serializer = OpenAiChatSessionSerializer(session)

    if request.method == 'POST':
        message = request.data.get('message')
        if not message:
            return Response(
                {'error': 'Message is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        session.send(message)

    return Response(serializer.data)