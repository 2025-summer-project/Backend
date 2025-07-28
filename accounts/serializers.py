from rest_framework import serializers
from django.utils import timezone
from datetime import datetime, timedelta
from core.models import User, RefreshTokenStore  # core.models에서 User 모델을 가져옴
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

# 사용자 회원가입에 사용할 시리얼라이저
class UserSerializer(serializers.ModelSerializer):
    # password는 write_only → 클라이언트에서 보내줄 수 있지만, 응답에서는 보이지 않음
    password = serializers.CharField(write_only=True)

    # 시리얼라이저 설정
    class Meta:
        model = User  # 어떤 모델을 기반으로 시리얼라이징할지 지정
        fields = ('user_id', 'user_name', 'password')  # 입력/출력 대상 필드

    # 유저를 생성할 때 호출되는 함수
    def create(self, validated_data):
        # create_user는 UserManager에 정의한 사용자 생성 함수 (비밀번호 해시 저장 포함)
        user = User.objects.create_user(
            user_id=validated_data['user_id'],
            user_name=validated_data['user_name'],
            password=validated_data['password']
        )
        return user
    

# JWT 로그인용 시리얼라이저

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):

    username_field = 'user_id'  

    # 요청 받을 필드
    user_id = serializers.CharField(write_only=True)
    password = serializers.CharField(write_only=True)

    # 응답으로 보여줄 필드
    access = serializers.CharField(read_only=True)
    refresh = serializers.CharField(read_only=True)
    user_name = serializers.CharField(read_only=True)

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['user_name'] = user.user_name
        return token
    
    def validate(self, attrs):
        attrs['username'] = attrs.get('user_id') # user_id → username 필드로 변환해서 부모 클래스가 인식
        data = super().validate(attrs)  # 기본 access/refresh 생성

        refresh = self.get_token(self.user)

        RefreshTokenStore.objects.filter(user=self.user).delete() # 기존 RefreshToken 제거

        # DB에 새로운 RefreshToken 저장
        RefreshTokenStore.objects.create(
            user=self.user,
            token=str(refresh),
            created_at=timezone.now(),
            expires_at=timezone.now() + timedelta(days=7)  # JWT exp와 맞추기
        )


        # 응답에 추가로 user_id와 user_name 포함
        data.update({
            "user_id": self.user.user_id,
            "user_name": self.user.user_name,
        })
        return data
   