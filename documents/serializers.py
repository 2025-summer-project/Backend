from rest_framework import serializers
from core.models import Document

class DocumentFileNameSerializer(serializers.ModelSerializer):
    class Meta:
        model = Document
        fields = ['file_name']