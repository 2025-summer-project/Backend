from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from core.models import Document
from documents.serializers import DocumentFileNameSerializer

# Swagger용 import
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi


class DocumentListView(APIView):
    permission_classes = [IsAuthenticated]  # JWT 인증 필요

    @swagger_auto_schema(
        operation_summary="문서 목록 조회",
        operation_description="로그인한 유저가 업로드한 문서 목록(file_name)을 반환합니다.",
        responses={200: DocumentFileNameSerializer(many=True)},
        security=[{"Bearer": []}]  # Swagger에서 Authorization 헤더 요구
        
    )
    def get(self, request):
        user = request.user
        documents = Document.objects.filter(user=user)
        serializer = DocumentFileNameSerializer(documents, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)