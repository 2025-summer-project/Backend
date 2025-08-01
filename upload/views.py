from rest_framework.parsers import MultiPartParser
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from core.models import Document
from core.models import User
import pdfplumber
from openai import OpenAI
from django.conf import settings
import os

# PDF 텍스트 추출 함수
def extract_text_from_pdf(file):
    text = ''   # 텍스트 담을 변수 
    with pdfplumber.open(file) as pdf:
        for page in pdf.pages:
            text += page.extract_text() or ''
    return text

# 요약 함수 
client = OpenAI(api_key=settings.OPENAI_API_KEY)

def summarize_text_with_openai(text):
    try:
        prompt = GUIDELINE_PROMPT.replace("{{context}}", "").replace("{{user_question}}", text)

        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "당신은 변호사입니다."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.5,
            max_tokens=1500,
        )

        result = response.choices[0].message.content.strip()
        print("✅ OpenAI 요약 성공:", result[:100])
        return result

    except Exception as e:
        print(f"❌ OpenAI 요약 실패: {e}")
        return ""

# PDF 문서 업로드 기능
class DocumentUploadView(APIView):
    # permission_classes = [IsAuthenticated]  # 장고에서 제공하는 권한 클래스
    parser_classes = [MultiPartParser]  # 파일 데이터를 안전하게 읽도록 도와주는 역할 

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
        user = User.objects.get(id=1)
        # user = request.user
        file = request.FILES.get('file')

        if not file:
            return Response({'error': '파일이 없습니다.'}, status=400)

        if not file.name.endswith('.pdf'):
            return Response({'error': 'PDF 파일만 업로드 가능합니다.'}, status=400)

        # 텍스트 자동 추출
        extracted_text = extract_text_from_pdf(file)
        summary_text = summarize_text_with_openai(extracted_text[:3000])

        file_name_only, _ = os.path.splitext(file.name)

        document = Document.objects.create(
            user=user,
            file=file,  # /media/documents 디렉터리에 저장됨 
            file_name=file_name_only,
            extracted_text=extracted_text,
            summary_text=summary_text,
            chat_name=file_name_only,
        )

        return Response({'message': '업로드 성공', 'document_id': document.id})
    
GUIDELINE_PROMPT = """
당신은 **근로 계약** 전문 변호사입니다. 
당신의 임무는 제공된 계약서를 기반으로 피계약자가 주의깊게 살펴보아야 할 주요 조항과 독소 조항, 그리고 모호한 표현들을 찾아내는 것입니다.
청자은 해당 계약서의 피계약자이며, 피계약자는 20살 이상의 성인이지만, 법률에 대한 지식이 계약자보다 상대적으로 부족한 사람입니다.

##규칙
계약서의 조항은 실제 법률에 근거하여 작성된 계약서의 내용뿐 아니라, 법률에 근거하지 않은 모든 내용을 포함합니다.
- **주요 조항** : 계약이 성사될 시 피계약자가 가장 중요하게 살펴봐야 하는 조항을 의미합니다.
- **독소 조항** : 계약이 성사될 시 피계약자에게 불리하게 작용할 수 있거나 법률에 어긋나는 조항을 의미합니다. 
- **모호한 표현** : 계약 체결 후 피계약자에게 잠재적 피해를 끼칠 수 있는 조항을 의미합니다.

당신은 계약서의 각 문장을 기준으로 가장 유사한 법률 조항을 찾아, 그에 어긋나는 표현이 있는지 파악해야 합니다. 
계약서의 내용과 법률 조항 간의 맥락을 파악하여 피계약자에게 불리하게 작용할 수 있는 모든 조항을 탐색합니다.
주요 조항, 독소 조항, 모호한 표현은 모두 법률 데이터를 기반으로, '왜' 중요한지, '왜' 어긋나는지, '왜' 모호한지 피계약자에게 명확하고, 구체적으로 설명해야 합니다.

계약서 상의 조건 및 조항을 법률과 비교하여 피계약자에게 불리한 점을 찾지 못했다면, 계약이 체결되어도 무방하다고 할 수 있습니다. 그러나 한 번 더 확인하는 것을 기본으로 합니다.

## 출력 형식
출력 형식은 JSON 형태로 각 key는 다음과 같이 구성되어야 합니다. 
- **sentence**: 주어진 계약서에 작성된 내용을 포함합니다.
- **types**: 배열 형태를 가지며, 'main'(주요 조항), 'toxin'(독소 조항), 'ambi'(모호한 표현) 중 1~3개를 가질 수 있습니다.
- **law**: "sentence"와 가장 유사도가 높은 실제 법률 조항을 의미합니다. 이를 출력할 때는 '000법 제00조0'와 같은 형식으로 출력합니다.
- **description**: "law"의 법률 데이터와 계약서 내용의 차이점을 설명합니다.
- **recommend**: "law"와 "description"에 따라 수정이 완료된 수정 조항입니다.

답안은 [] 내부에 작성되어야 하며, JSON만 제공합니다.

## 질문
1. 이 계약서의 주요 조항은 모두 무엇입니까? 주요 조항을 찾고 'main' 타입으로 분류하여, 각 조항이 중요한 이유를 설명하십시오.
2. 이 계약서에서 독소 조항은 모두 무엇입니까? 독소 조항을 찾고 'toxin' 타입으로 분류하여, 각 조항이 피계약자에게 불리한 이유를 설명하십시오.
3. 이 계약서에서 모호한 표현은 모두 무엇입니까? 모호한 표현을 찾고 'ambi' 타입으로 분류하여, 각 표현이 모호한 이유와 그로 인한 잠재적 피해를 설명하십시오.

## 입력 데이터
- Context: {{context}}
- 계약서: {{user_question}}
"""