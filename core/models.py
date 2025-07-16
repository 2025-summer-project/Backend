from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager


# 사용자 생성 시 필요한 함수 정의
class UserManager(BaseUserManager):
    def create_user(self, user_id, user_name, password=None):
        if not user_id:
            raise ValueError("아이디는 필수입니다.")
        if not user_name:
            raise ValueError("이름은 필수입니다.")
        if not password:
            raise ValueError("비밀번호는 필수입니다.")
        user = self.model(user_id=user_id, user_name=user_name)
        user.set_password(password)  # 비밀번호 해시 저장
        user.save(using=self._db)
        return user


# 사용자 모델
class User(AbstractBaseUser):
    user_id = models.CharField(max_length=20, unique=True)   # 로그인용 ID
    user_name = models.CharField(max_length=20)              # 사용자 이름
    password = models.CharField(max_length=128)              # 해시 저장

    created_at = models.DateTimeField(auto_now_add=True)     # 생성일

    USERNAME_FIELD = 'user_id'            # 로그인 ID 필드

    objects = UserManager()               # 사용자 매니저 지정

    def __str__(self):
        return self.user_id


# 문서 모델
class Document(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)     # 문서 주인

    file = models.FileField(upload_to='documents/')              # 실제 파일
    file_name = models.CharField(max_length=255)                 # 파일명
    chat_name = models.CharField(max_length=255)                 # 채팅방 이름

    extracted_text = models.TextField()                          # 추출된 원문 텍스트
    summary_text = models.TextField()                            # 요약된 텍스트

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.file_name or 'Unnamed'} - {self.user.user_id}"


# 대화 로그 모델
class ChatLog(models.Model):
    document = models.ForeignKey(Document, on_delete=models.CASCADE)  # 어떤 문서에 대한 대화인지
    user = models.ForeignKey(User, on_delete=models.CASCADE)          # 어떤 사용자의 메시지인지

    sender = models.CharField(                                       # 누가 보냈는지
        max_length=10,
        choices=[('ai', 'AI'), ('user', 'User')]
    )
    message = models.TextField(null=True, blank=True)               # 메시지 내용
    created_at = models.DateTimeField(auto_now_add=True)            # 대화 시각

    def __str__(self):
        return f"{self.sender}: {self.message[:30]}"