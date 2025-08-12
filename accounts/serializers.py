from rest_framework import serializers
from django.utils import timezone
from datetime import datetime, timedelta
from django.db import transaction, IntegrityError
from core.models import User, RefreshTokenStore  # core.models에서 User 모델을 가져옴
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.conf import settings

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

    # 응답 필드
    access = serializers.CharField(read_only=True)
    refresh = serializers.CharField(read_only=True)
    user_name = serializers.CharField(read_only=True)

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['user_name'] = user.user_name
        return token

    @transaction.atomic
    def validate(self, attrs):
        attrs['username'] = attrs.get('user_id')
        data = super().validate(attrs)

        # 새 refresh 생성
        refresh = self.get_token(self.user)

        # 만료 시간 설정 (settings에서 가져오거나 기본 7일)
        lifetime = getattr(settings, "SIMPLE_JWT", {}).get("REFRESH_TOKEN_LIFETIME", timedelta(days=7))
        expires = timezone.now() + lifetime

        # 만료 토큰 삭제
        RefreshTokenStore.objects.filter(
            user=self.user, expires_at__lt=timezone.now()
        ).delete()

        # 유저당 1개만 유지
        try:
            RefreshTokenStore.objects.update_or_create(
                user=self.user,
                defaults={
                    "token": str(refresh),
                    "expires_at": expires,
                    "revoked": False,
                }
            )
        except IntegrityError:
            RefreshTokenStore.objects.filter(user=self.user).delete()
            RefreshTokenStore.objects.create(
                user=self.user,
                token=str(refresh),
                expires_at=expires,
                revoked=False,
            )

        # 응답 데이터 확장
        data.update({
            "user_id": self.user.user_id,
            "user_name": self.user.user_name,
        })
        return data

    