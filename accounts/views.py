from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework import serializers
from core.models import RefreshTokenStore
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
        
# 로그인 요청 처리
class LoginView(TokenObtainPairView):
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
    
# 로그아웃 요청 처리   
class LogoutView(APIView):

    @swagger_auto_schema(
        operation_summary="로그아웃",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=["refresh"],
            properties={
                "refresh": openapi.Schema(type=openapi.TYPE_STRING, description="리프레시 토큰"),
            }
        ),
        responses={
            200: "로그아웃 성공",
            400: "요청 에러",
        }
    )    

    def post(self, request):
        refresh_token = request.data.get("refresh")

        if not refresh_token:
            return Response({"detail": "refresh 토큰이 필요합니다."}, status=400)

        deleted_count, _ = RefreshTokenStore.objects.filter(token=refresh_token).delete()
        
        if deleted_count:
            return Response({"detail": "로그아웃 성공"}, status=200)
        else:
           return Response({"detail": "해당 토큰이 존재하지 않거나 이미 삭제됨"}, status=400)