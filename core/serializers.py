from rest_framework import serializers
from .models import User  # core.models에서 User 모델을 가져옴

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
