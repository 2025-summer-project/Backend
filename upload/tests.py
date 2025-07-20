from django.test import TestCase
from rest_framework.parsers import MultiPartParser
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from core.models import Document
from core.models import User

# PDF 문서 업로드 기능
class DocumentUploadView(APIView):
    # 로그인 api 추가되면 주석 삭제하면 됨 
    # permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser]

    @swagger_auto_schema(
        operation_summary="PDF 문서 업로드 API",
        manual_parameters=[
            openapi.Parameter(
                'file', openapi.IN_FORM,  # form-data에 들어가는 값
                description="업로드할 PDF 파일",
                type=openapi.TYPE_FILE,
                required=True
            ),
        ]
    )

    # 클라이언트가 보낸 파일 받아오기
    def post(self, request):
        user = User.objects.get(user_id='testuser')
        # user = request.user
        file = request.FILES.get('file')

        if not file:
            return Response({'error': '파일이 없습니다.'}, status=400)

        if not file.name.endswith('.pdf'):
            return Response({'error': 'PDF 파일만 업로드 가능합니다.'}, status=400)

        document = Document.objects.create(
            user=user,
            file=file,  # /media/documents 디렉터리에 저장됨 
            file_name=file.name,
            extracted_text='',
            summary_text='',
            chat_name=''
        )

        return Response({'message': '업로드 성공', 'document_id': document.id})