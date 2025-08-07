from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from core.models import ChatLog, Document
from openai import OpenAI
from django.conf import settings
from rest_framework.exceptions import AuthenticationFailed, NotAuthenticated
from django.utils import timezone

# Swagger 스키마 정의
chat_request_schema = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    required=["document_id", "message"],
    properties={
        "document_id": openapi.Schema(type=openapi.TYPE_INTEGER, description="문서 ID"),
        "message": openapi.Schema(type=openapi.TYPE_STRING, description="사용자가 보낸 메시지 내용"),
    },
)

chat_response_schema = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        "user_message": openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "id": openapi.Schema(type=openapi.TYPE_INTEGER, description="사용자 메시지 ID"),
                "message": openapi.Schema(type=openapi.TYPE_STRING, description="사용자 메시지 내용"),
            }
        ),
        "ai_message": openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "id": openapi.Schema(type=openapi.TYPE_INTEGER, description="AI 메시지 ID"),
                "message": openapi.Schema(type=openapi.TYPE_STRING, description="AI 응답 메시지 내용"),
            }
        ),
    },
)

# OpenAI API를 호출하여 메시지에 대한 AI 응답 생성
client = OpenAI(api_key=settings.OPENAI_API_KEY)

def call_openai_api(message: str) -> str:
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a helpful AI assistant specialized in legal contract review. 모든 답변은 한국어로 제공하세요."},
                {"role": "user", "content": message}
            ],
            max_tokens=500,
            temperature=0.2
        )
        result = response.choices[0].message.content.strip()
        print("OpenAI 요약 성공:", result[:100])
        return result

    except Exception as e:
        print(f"OpenAI 호출 실패: {type(e).__name__} - {e}")
        return "AI 응답 생성에 실패했습니다. 다시 시도해주세요."

class ChatCreateView(APIView):
    permission_classes = [IsAuthenticated]  # 로그인 사용자만 접근 가능

    def handle_exception(self, exc):
        # 토큰 만료 또는 인증 실패 시 사용자 친화적인 메시지 반환
        if isinstance(exc, (AuthenticationFailed, NotAuthenticated)):
            return Response(
                {"detail": "액세스 토큰이 만료되었거나 유효하지 않습니다."},
                status=status.HTTP_401_UNAUTHORIZED
            )
        return super().handle_exception(exc)

    @swagger_auto_schema(
        operation_summary="대화 내용 저장",
        request_body=chat_request_schema,
        responses={200: chat_response_schema, 400: "잘못된 요청", 401: "토큰 만료", 404: "문서 없음"}
    )
    def post(selt, request):
        document_id = request.data.get('document_id')
        message = request.data.get('message')

        if not document_id or not message:
            return Response(
                {"error": "document_id, message는 필수 입력 항목입니다."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            document = Document.objects.get(id=document_id, user=request.user)
        except Document.DoesNotExist:
            return Response({"error": "해당 문서를 찾을 수 없습니다."}, status=status.HTTP_404_NOT_FOUND)

        # 사용자 메시지 저장
        user_message = ChatLog.objects.create(
        document=document,
        user=request.user,
        sender="user",
        message=message
        )

        # AI 응답 생성
        ai_answer = call_openai_api(message)  # OpenAI 호출 로직
        ai_message = ChatLog.objects.create(
        document=document,
        user=request.user,
        sender="ai",
        message=ai_answer
        )   

        return Response({
            "user_message": {"id": user_message.id, "message": message},
            "ai_message": {"id": ai_message.id, "message": ai_answer}
        }, status=status.HTTP_200_OK)
    
# 문서별 채팅 조회
class ChatHistoryView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="문서별 대화 히스토리 조회",
        responses={
            200: openapi.Response(
                description="대화 히스토리",
                examples={
                    "application/json": {
                        "document_id": 1,
                        "chats": [
                            {"id": 1, "sender": "user", "message": "안녕하세요"},
                            {"id": 2, "sender": "ai", "message": "안녕하세요! 무엇을 도와드릴까요?"}
                        ]
                    }
                }
            ),
            401: openapi.Response(description="인증 실패 또는 토큰 만료"),
            404: openapi.Response(description="문서 없음")
        }
    )
    def get(self, request, document_id):
        try:
            document = Document.objects.get(id=document_id, user=request.user)
        except Document.DoesNotExist:
            return Response({"error": "해당 문서를 찾을 수 없습니다."}, status=404)

        chats = ChatLog.objects.filter(document=document).order_by("id")
        chat_list = [{"id": c.id, "sender": c.sender, "message": c.message, "created_at": timezone.localtime(c.created_at).isoformat()} for c in chats]

        return Response({
            "document_id": document.id,
            "chats": chat_list,
        }, status=200)
    

# 요약본 PDF 조회
from django.http import HttpResponse

class SummaryPDFView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="요약본 PDF 다운로드",
        responses={
            200: openapi.Response(
                description="PDF 파일 반환",
                schema=openapi.Schema(type=openapi.TYPE_STRING, format='binary')
            ),
            404: openapi.Response(description="문서 없음"),
            401: openapi.Response(description="인증 실패 또는 토큰 만료")
        }
    )
    def get(self, request, document_id):
        try:
            document = Document.objects.get(id=document_id, user=request.user)
        except Document.DoesNotExist:
            return Response({"error": "해당 문서를 찾을 수 없습니다."}, status=404)

        if not document.summary_file:
            return Response({"error": "요약 PDF 파일이 존재하지 않습니다."}, status=404)

        try:
            with document.summary_file.open("rb") as pdf_file:
                response = HttpResponse(pdf_file.read(), content_type="application/pdf")
                filename = f"{document.file_name}_요약본.pdf"
                response["Content-Disposition"] = f'attachment; filename="{filename}"'
                return response
        except Exception as e:
            return Response({"error": f"PDF 파일을 읽는 도중 오류가 발생했습니다: {str(e)}"}, status=500)
