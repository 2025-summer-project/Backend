from rest_framework import serializers
from core.models import Document

class FileNameViewSerializer(serializers.ModelSerializer):
    class Meta:
        model = Document
        fields = ['file_name']

class ChatNameViewSerializer(serializers.ModelSerializer):
    class Meta:
        model = Document
        fields = ['chat_name']

class FileNameUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Document
        fields = ['file_name']

    def validate_file_name(self, value):
        if not value.strip():
            raise serializers.ValidationError("파일 이름은 비워둘 수 없습니다.")
        return value        

class ChatNameUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Document
        fields = ['chat_name']

    def validate_file_name(self, value):
        if not value.strip():
            raise serializers.ValidationError("채팅방 이름은 비워둘 수 없습니다.")
        return value        
      