from rest_framework import serializers
from core.models import OpenAiChatSession


class OpenAiChatSessionMessageSerializer(serializers.Serializer):
    """ Represents the messages that're sent to & from the API.
        That'll be the role & the content that is sent with every message & received from the messages
        from the AI Chatbot.
        Serializer converts that to JSON & vice-versa.
    """
    role = serializers.CharField()
    content = serializers.CharField()


class OpenAiChatSessionSerializer(serializers.ModelSerializer):
    messages = OpenAiChatSessionMessageSerializer(many=True)

    def to_representation(self, instance):
        """ Takes our instance & it gets the messages """
        representation = super().to_representation(instance)
        representation['messages'] = [
            msg for msg in representation['messages']
            if msg['role'] != 'system'
        ]

        return representation

    class Meta:
        model = OpenAiChatSession
        fields = ['id', 'messages']
        read_only_fields = ["messages"]

