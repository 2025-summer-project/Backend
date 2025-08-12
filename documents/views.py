from django.shortcuts import render, get_object_or_404
from django.http import FileResponse

from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from core.models import Document
from documents.serializers import (
    FileNameViewSerializer,
    FileNameUpdateSerializer,
    ChatNameViewSerializer,
    ChatNameUpdateSerializer,
    SummaryFileSerializer
)

# 문서 목록 조회
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

# 요약된 문서 목록 조회
class SummaryListView(APIView):
    permission_classes = [IsAuthenticated]  # JWT 인증 필요

    @swagger_auto_schema(
        operation_summary="요약된 문서 목록 조회",
        operation_description="로그인한 유저의 문서에서 summary_file만 반환합니다.",
        responses={200: SummaryFileSerializer(many=True)},
        security=[{"Bearer": []}],
    )
    def get(self, request):
        user = request.user
        documents = (
            Document.objects
            .filter(user=user)
            .order_by('-updated_at', '-created_at')
        )
        serializer = SummaryFileSerializer(documents, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
# 채팅방 목록 조회
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
    

#문서 목록 이름 변경    
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


# 채팅방 이름 변경
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


# 원본 문서 PDF 조회
class DocumentPDFView(APIView):
    permission_classes = [IsAuthenticated]  # JWT 인증 필요

    @swagger_auto_schema(
        operation_summary="문서 PDF 보기",
        operation_description="해당 문서의 PDF 파일을 반환합니다 (inline).",
        
        responses={200: 'application/pdf'},
        security=[{"Bearer": []}],
    )
    def get(self, request, document_id: int):
        # 1) 유저 소유 문서만
        try:
            doc = Document.objects.get(pk=document_id, user=request.user)
        except Document.DoesNotExist:
            return Response({"detail": "문서를 찾을 수 없습니다."}, status=status.HTTP_404_NOT_FOUND)

        # 2) PDF 파일 필드 찾기 (모델 필드명에 맞춰 조정)
        file_field = None
        for attr in ("pdf_file", "file", "uploaded_file"):
            if hasattr(doc, attr):
                file_field = getattr(doc, attr)
                break
        if not file_field:
            return Response({"detail": "PDF 파일 필드가 없습니다."}, status=400)
        if not file_field:  # 파일이 비어있을 때
            return Response({"detail": "파일이 존재하지 않습니다."}, status=404)

        # 3) 파일 열기(로컬/스토리지 모두 대응)
        try:
            file_field.open('rb')
            fileobj = file_field.file 
        except Exception:
            fileobj = getattr(file_field, 'file', None) or file_field

        # 4) 파일 스트리밍 응답
        resp = FileResponse(fileobj, content_type='application/pdf')

        # 파일명: 모델에 file_name이 있으면 사용, 아니면 업로드 이름
        filename = getattr(doc, 'file_name', None) or getattr(file_field, 'name', 'document.pdf')
        if not str(filename).lower().endswith('.pdf'):
            filename = f"{filename}.pdf"
        resp['Content-Disposition'] = f'inline; filename="{filename}"'
        return resp        