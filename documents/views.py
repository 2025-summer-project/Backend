from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from core.models import Document
from documents.serializers import FileNameViewSerializer, FileNameUpdateSerializer, ChatNameViewSerializer, ChatNameUpdateSerializer

# Swagger용 import
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi


class DocumentListView(APIView):
    permission_classes = [IsAuthenticated]  # JWT 인증 필요

    @swagger_auto_schema(
        operation_summary="문서 목록 조회",
        operation_description="로그인한 유저가 업로드한 문서 목록(file_name)을 반환합니다.",
        responses={200: FileNameViewSerializer(many=True)},
        security=[{"Bearer": []}]  # Swagger에서 Authorization 헤더 요구
        
    )
    def get(self, request):
        user = request.user
        documents = Document.objects.filter(user=user)
        serializer = FileNameViewSerializer(documents, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    

class ChatListView(APIView):
    permission_classes = [IsAuthenticated]  # JWT 인증 필요

    @swagger_auto_schema(
        operation_summary="채팅방 목록 조회",
        operation_description="로그인한 유저의 채팅방 목록(chat_name)을 반환합니다.",
        responses={200: ChatNameViewSerializer(many=True)},
        security=[{"Bearer": []}]  # Swagger에서 Authorization 헤더 요구
        
    )
    def get(self, request):
        user = request.user
        documents = Document.objects.filter(user=user)
        serializer = ChatNameViewSerializer(documents, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    
class UpdateFileNameView(APIView):
    permission_classes = [IsAuthenticated]  # JWT 인증 필요

    @swagger_auto_schema(
        operation_summary="문서 이름 변경",
        operation_description="문서의 file_name 변경 (확장자 제외 이름 수정)",
        request_body=FileNameUpdateSerializer,
        responses={200: openapi.Response("성공", FileNameUpdateSerializer)}
    )
    def patch(self, request, pk):
        try:
            document = Document.objects.get(pk=pk, user=request.user)
        except Document.DoesNotExist:
            return Response({"error": "문서를 찾을 수 없습니다."}, status=404)

        serializer = FileNameUpdateSerializer(document, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({
                "message": "파일 이름이 변경되었습니다.",
                "data": serializer.data
            }, status=200)
        return Response(serializer.errors, status=400)    


class UpdateChatNameView(APIView):
    permission_classes = [IsAuthenticated]  # JWT 인증 필요

    @swagger_auto_schema(
        operation_summary="채팅방 이름 변경",
        operation_description="문서의 chat_name 변경 (확장자 제외 이름 수정)",
        request_body=ChatNameUpdateSerializer,
        responses={200: openapi.Response("성공", ChatNameUpdateSerializer)}
    )
    def patch(self, request, pk):
        try:
            document = Document.objects.get(pk=pk, user=request.user)
        except Document.DoesNotExist:
            return Response({"error": "채팅방을 찾을 수 없습니다."}, status=404)

        serializer = ChatNameUpdateSerializer(document, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({
                "message": "채팅방 이름이 변경되었습니다.",
                "data": serializer.data
            }, status=200)
        return Response(serializer.errors, status=400)        