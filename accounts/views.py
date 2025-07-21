from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework import serializers
from rest_framework_simplejwt.views import TokenObtainPairView
from .serializers import CustomTokenObtainPairSerializer
from accounts.serializers import UserSerializer  # 시리얼라이저 불러오기

# Swagger용 데코레이터 추가
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from django.utils.decorators import method_decorator

# 회원가입 요청을 처리하는 API 뷰
class SignupView(APIView):
     #Swagger가 인식할 수 있게 데코레이터 사용
    @swagger_auto_schema(
        request_body=UserSerializer,  #이게 있어야 Swagger 입력창이 뜬다
        responses={201: openapi.Response('회원가입 완료')}
    )
    
    def post(self, request):
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            print("유효성 통과")  # 콘솔에 찍힘
            serializer.save()
            return Response({"message": "회원가입 성공!"}, status=201)
        else:
            print("유효성 실패:", serializer.errors)  # 실패 시 오류 로그 확인
            return Response(serializer.errors, status=400)
        
# JWT 로그인
#token_obtain_schema = swagger_auto_schema(
   # operation_summary="JWT 로그인",
   # request_body=CustomTokenObtainPairSerializer,
    #responses={200: openapi.Response("로그인 성공")},
#)

#@method_decorator(token_obtain_schema, name='post')
class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer

    @swagger_auto_schema(
        operation_summary="JWT 로그인",
        request_body=CustomTokenObtainPairSerializer,  # 입력은 그대로
        responses={
            200: openapi.Response(
                description="로그인 성공",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "access": openapi.Schema(type=openapi.TYPE_STRING, description="Access 토큰"),
                        "refresh": openapi.Schema(type=openapi.TYPE_STRING, description="Refresh 토큰"),
                        "user_id": openapi.Schema(type=openapi.TYPE_STRING, description="사용자 ID"),
                        "user_name": openapi.Schema(type=openapi.TYPE_STRING, description="사용자 이름"),
                    },
                    required=["access", "refresh"]
                )
            ),
            401: openapi.Response(description="로그인 실패 (비밀번호 틀림, 사용자 없음 등)"),
        }
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)