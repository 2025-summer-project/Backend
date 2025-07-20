from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from core.serializers import UserSerializer  # 시리얼라이저 불러오기
# Swagger용 데코레이터 추가
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

# 회원가입 요청을 처리하는 API 뷰
class SignupView(APIView):
     #Swagger가 인식할 수 있게 데코레이터 사용
    @swagger_auto_schema(
        request_body=UserSerializer,  #이게 있어야 Swagger 입력창이 뜬다
        responses={201: openapi.Response('회원가입 완료')}
    )
    def post(self, request):
        # 요청 JSON 데이터를 UserSerializer에 전달
        serializer = UserSerializer(data=request.data)

        if serializer.is_valid():  # 데이터 유효성 검사
            serializer.save()  # create() 실행 → create_user() 호출됨
            return Response({"message": "회원가입 성공!"}, status=status.HTTP_201_CREATED)
        
        # 유효성 오류 시 에러 메시지 반환
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    

    def post(self, request):
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            print("✅ 유효성 통과")  # 콘솔에 찍힘
            serializer.save()
            return Response({"message": "회원가입 성공!"}, status=201)
        else:
            print("❌ 유효성 실패:", serializer.errors)  # 실패 시 오류 로그 확인
            return Response(serializer.errors, status=400)
