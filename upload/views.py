from rest_framework.parsers import MultiPartParser
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from core.models import Document
import pdfplumber
from openai import OpenAI
from django.conf import settings
import os
from rest_framework.exceptions import AuthenticationFailed, NotAuthenticated
from rest_framework import status
import json
from django.core.files.base import ContentFile
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, KeepTogether, PageBreak
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import io
from datetime import datetime

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
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a helpful AI assistant specialized in legal contract review. 모든 답변은 한국어로 제공하세요."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.5,
            max_tokens=2500,
        )

        result = response.choices[0].message.content.strip()
        result = result.replace("```json", "").replace("```", "").strip()  # 백틱 제거
        print("✅ GPT 원본 응답:", repr(result[:1000]))
        return result

    except Exception as e:
        print(f"OpenAI 요약 실패: {e}")
        return ""

# 요약 결과가 JSON 형식인지 확인하는 함수
def validate_summary_json(json_text):
    try:
        parsed = json.loads(json_text)  # 문자열을 JSON으로 파싱
        if not isinstance(parsed, list):  # 리스트 형식이 아닌 경우 예외 발생
            raise ValueError("요약 데이터는 리스트가 아닙니다.")
        return True  # 유효한 JSON
    except json.JSONDecodeError:
        return False  # 파싱 실패

# 요약 JSON을 PDF 템플릿용 컨텍스트로 변환
from collections import Counter

def build_summary_context(items):
    # items: 모델이 반환한 JSON 배열(list of dict)
    # 통계 집계
    total = len(items)
    type_counts = Counter()
    risk_counts = Counter()
    clauses = []

    for it in items:
        types = it.get("types", []) or []
        for t in types:
            type_counts[t] += 1
        risk = (it.get("risk") or "low").lower()
        if risk not in ("low", "mid", "high"):
            risk = "low"
        risk_counts[risk] += 1

        clauses.append({
            "title": it.get("title") or it.get("category") or "조항",
            "risk": risk,
            "original": it.get("sentence", ""),
            "law": it.get("law", "-"),
            "commentary": it.get("description", "-"),
            "recommendation": it.get("recommend", "-"),
            "types": types,
        })

    # 하이라이트: 독소+High 우선, 부족하면 Mid 보충 (최대 5)
    highlights = [f"[{c['title']}] {c['commentary']}" for c in clauses if ("toxin" in c["types"]) and c["risk"] == "high"]
    if len(highlights) < 5:
        highlights += [f"[{c['title']}] {c['commentary']}" for c in clauses if ("toxin" in c["types"]) and c["risk"] == "mid"]
    highlights = highlights[:5]

    stats = {
        "total": total,
        "main": type_counts.get("main", 0),
        "toxin": type_counts.get("toxin", 0),
        "ambi": type_counts.get("ambi", 0),
        "risk_high": risk_counts.get("high", 0),
        "risk_mid": risk_counts.get("mid", 0),
        "risk_low": risk_counts.get("low", 0),
    }

    return stats, highlights, clauses

# PDF 문서 업로드 기능
class DocumentUploadView(APIView):
    permission_classes = [IsAuthenticated]  # 장고에서 제공하는 권한 클래스
    parser_classes = [MultiPartParser]  # 파일 데이터를 안전하게 읽도록 도와주는 역할 

    def handle_exception(self, exc):
        if isinstance(exc, (AuthenticationFailed, NotAuthenticated)):
            return Response(
                {"detail": "액세스 토큰이 만료되었거나 유효하지 않습니다."},
                status=status.HTTP_401_UNAUTHORIZED
            )
        return super().handle_exception(exc)

    @swagger_auto_schema(
        operation_summary="PDF 문서 업로드",
        manual_parameters=[
            openapi.Parameter(
                'file', openapi.IN_FORM,  # form-data에 들어가는 값
                description="업로드할 PDF 파일",
                type=openapi.TYPE_FILE,
                required=True
            ),
        ],
        responses={
            200: openapi.Response('업로드 성공'),
            400: openapi.Response('요청 오류'),
            401: openapi.Response('액세스 토큰 만료 또는 유효하지 않음'),
        }
    )

    # 클라이언트가 보낸 파일 받아오기
    def post(self, request):
        user = request.user
        file = request.FILES.get('file')

        if not file:
            return Response({'error': '파일이 없습니다.'}, status=400)

        if not file.name.endswith('.pdf'):
            return Response({'error': 'PDF 파일만 업로드 가능합니다.'}, status=400)

        # 텍스트 자동 추출
        extracted_text = extract_text_from_pdf(file)
        summary_text = summarize_text_with_openai(extracted_text[:3000])

        # 요약 결과가 유효한 JSON인지 검사
        if not validate_summary_json(summary_text):
            return Response({'error': 'OpenAI 요약 결과가 유효한 JSON 형식이 아닙니다.'}, status=400)

        timestamp = datetime.now().strftime("%Y.%m.%d_%H:%M")
        filename,  = os.path.splitext(file.name)
        file_name_only = f"{filename}{timestamp}"

        # Register fonts
        pdfmetrics.registerFont(TTFont('NanumGothic', 'fonts/NanumGothic-Regular.ttf'))
        pdfmetrics.registerFont(TTFont('NanumGothic-Bold', 'fonts/NanumGothic-Bold.ttf'))
        pdfmetrics.registerFont(TTFont('NanumGothic-ExtraBold', 'fonts/NanumGothic-ExtraBold.ttf'))

        # Create PDF from summary JSON
        summary_data = json.loads(summary_text)
        highlights, clauses = build_summary_context(summary_data)

        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        styles = getSampleStyleSheet()
        styles.add(ParagraphStyle(name='H1', parent=styles['Normal'], fontName='NanumGothic-ExtraBold', fontSize=18, spaceAfter=12))
        styles.add(ParagraphStyle(name='H2', parent=styles['Normal'], fontName='NanumGothic-Bold', fontSize=14, spaceBefore=6, spaceAfter=6))
        styles.add(ParagraphStyle(name='Label', parent=styles['Normal'], fontName='NanumGothic-Bold', fontSize=11, textColor=colors.HexColor('#374151'), spaceBefore=4, spaceAfter=2))
        styles.add(ParagraphStyle(name='Body', parent=styles['Normal'], fontName='NanumGothic', fontSize=11, leading=16))
        styles.add(ParagraphStyle(name='Quote', parent=styles['Normal'], fontName='NanumGothic', fontSize=10.5, backColor=colors.HexColor('#F9FAFB'), borderWidth=1, borderColor=colors.HexColor('#E5E7EB'), borderPadding=6, leading=15))

        def risk_badge(text, risk):
            # 작은 1행 테이블로 배지 스타일 구성
            bg = {'low': colors.HexColor('#E8F5E9'), 'mid': colors.HexColor('#FFF3E0'), 'high': colors.HexColor('#FFEBEE')}.get(risk, colors.whitesmoke)
            fg = {'low': colors.HexColor('#1B5E20'), 'mid': colors.HexColor('#E65100'), 'high': colors.HexColor('#B71C1C')}.get(risk, colors.black)
            t = Table([[Paragraph(text, ParagraphStyle(name='Badge', fontName='NanumGothic-Bold', fontSize=9, textColor=fg))]], colWidths=[45])
            t.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,-1), bg),
                ('BOX', (0,0), (-1,-1), 0.5, bg),
                ('INNERPADDING', (0,0), (-1,-1), 3),
            ]))
            return t

        def divider():
            line = Table([['']], colWidths=['*'], rowHeights=[1])
            line.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#E5E7EB')),
            ]))
            return line

        elements = []
        # 문서 제목
        elements.append(Paragraph(f"{file_name_only} 요약본", styles['H1']))
        elements.append(divider())
        elements.append(Spacer(1, 8))

        if highlights:
            elements.append(Spacer(1, 10))
            elements.append(Paragraph('핵심 시정 권고', styles['H2']))
            for h in highlights[:5]:
                elements.append(Paragraph(f"• {h}", styles['Body']))

        elements.append(Spacer(1, 12))
        elements.append(divider())
        elements.append(Spacer(1, 8))
        elements.append(Paragraph('조항별 분석', styles['H2']))

        # 조항 카드 반복
        for idx, c in enumerate(clauses, 1):
            header = Table([[Paragraph(f"[{idx}] {c['title']}", styles['H2']), risk_badge(c['risk'].upper(), c['risk'])]], colWidths=['*', 55])
            header.setStyle(TableStyle([
                ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
                ('ALIGN', (1,0), (1,0), 'RIGHT'),
            ]))

            # 섹션 블록들(원문/법령/해설/개선안)
            blocks = []
            blocks.append(Paragraph('원문', styles['Label']))
            blocks.append(Paragraph(f"\"{c['original']}\"", styles['Body']))
            blocks.append(Paragraph('관련 법령', styles['Label']))
            blocks.append(Paragraph(c['law'], styles['Body']))
            blocks.append(Paragraph('해설', styles['Label']))
            blocks.append(Paragraph(c['commentary'], styles['Body']))
            blocks.append(Paragraph('개선안', styles['Label']))
            blocks.append(Paragraph(c['recommendation'], styles['Body']))

            elements.append(KeepTogether([header] + blocks + [Spacer(1, 10)]))

        doc.build(elements)
        buffer.seek(0)

        summary_file_name = f"{file_name_only}_요약본.pdf"
        summary_content = ContentFile(buffer.read(), name=summary_file_name)

        # 원본 계약서 PDF 저장
        # 요약본 PDF 저장 (AI 분석 결과)
        document = Document.objects.create(
            user=user,
            file=file,  # 원본 계약서 PDF 저장
            summary_file=summary_content,  # 요약본 PDF 저장
            file_name=file_name_only,
            extracted_text=extracted_text,
            chat_name=file_name_only,
        )

        return Response({'message': '업로드 성공', 'document_id': document.id}, status=200)
    
GUIDELINE_PROMPT = """
당신은 **근로 계약** 전문 변호사입니다.
당신의 임무는 제공된 계약서를 기반으로 피계약자가 주의깊게 살펴보아야 할 주요 조항과 독소 조항, 그리고 모호한 표현들을 찾아내는 것입니다.
청자는 해당 계약서의 피계약자이며, 피계약자는 20살 이상의 성인이지만, 법률에 대한 지식이 계약자보다 상대적으로 부족한 사람입니다.

## 규칙
계약서의 조항은 실제 법률에 근거한 내용뿐 아니라, 법률에 근거하지 않은 모든 내용을 포함합니다.
- **주요 조항(main)**: 계약이 성사될 시 피계약자가 가장 중요하게 살펴봐야 하는 조항
- **독소 조항(toxin)**: 피계약자에게 불리하게 작용할 수 있거나 법률에 어긋나는 조항
- **모호한 표현(ambi)**: 체결 후 피계약자에게 잠재적 피해를 끼칠 수 있는 모호한 표현

당신은 계약서의 각 문장을 기준으로 가장 유사한 법률 조항을 찾아, 그에 어긋나는 표현이 있는지 파악해야 합니다.
계약서 내용과 법률 조항 간의 맥락을 파악하여 피계약자에게 불리하게 작용할 수 있는 모든 조항을 탐색합니다.
각 항목은 '왜 중요한지', '왜 어긋나는지', '왜 모호한지'를 법률 데이터에 근거해 명확하고 구체적으로 설명하십시오.

## 출력 형식 (반드시 아래 스키마만 따르며, JSON 배열 외 텍스트 금지)
각 요소는 다음 키를 포함해야 합니다.
- **sentence**: 계약서 원문 문장
- **types**: 배열; 'main', 'toxin', 'ambi' 중 1~3개
- **law**: 가장 유사한 실제 법률 조항 (예: "근로기준법 제50조")
- **description**: 법률과 계약서 내용의 차이/위험을 설명
- **recommend**: description을 반영해 수정된 권장 조항을 제시
- **title**: 조항의 짧은 제목 (예: "근무시간", "계약기간", "해지")
- **risk**: 'low' | 'mid' | 'high' (피계약자 관점 위험도)
- **category**: 상위 분류 (예: "근로시간", "휴일", "비밀유지", "계약해지" 등)

요구사항: 유효한 JSON **배열**로만 답변하십시오. 코드 블록 표기(백틱 등)와 JSON 외 텍스트를 절대 포함하지 마십시오.

## 질문
1) 이 계약서의 주요 조항은 무엇입니까? 각각 'main' 타입으로 분류하고, 중요한 이유를 설명하십시오.
2) 이 계약서의 독소 조항은 무엇입니까? 각각 'toxin' 타입으로 분류하고, 불리한 이유를 설명하십시오.
3) 이 계약서의 모호한 표현은 무엇입니까? 각각 'ambi' 타입으로 분류하고, 모호한 이유와 잠재적 피해를 설명하십시오.

## 입력 데이터
- Context: {{context}}
- 계약서: {{user_question}}
"""