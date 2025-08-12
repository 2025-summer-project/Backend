from django.db import models
from django.utils import timezone
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin


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
class User(AbstractBaseUser, PermissionsMixin):
    user_id = models.CharField(max_length=20, unique=True)   # 로그인용 ID
    user_name = models.CharField(max_length=20)              # 사용자 이름
    password = models.CharField(max_length=128)              # 해시 저장
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)     # 생성일

    USERNAME_FIELD = 'user_id'            # 로그인 ID 필드
    REQUIRED_FIELDS = ['user_name']

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
    summary_file = models.FileField(upload_to='summaries/', blank=True, null=True)                        # 요약된 파일

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.file_name or 'Unnamed'} - {self.user.user_id}"


# 대화 로그 모델
class ChatLog(models.Model):
    document = models.ForeignKey(Document, on_delete=models.CASCADE)    # 어떤 문서에 대한 대화인지
    user = models.ForeignKey(User, on_delete=models.CASCADE)            # 어떤 사용자의 메시지인지

    sender = models.CharField(                                          # 누가 보냈는지
        max_length=10,
        choices=[('ai', 'AI'), ('user', 'User')]
    )
    message = models.TextField(null=True, blank=True)                   # 메시지 내용
    created_at = models.DateTimeField(auto_now_add=True)                # 대화 시각

    def __str__(self):
        return f"{self.sender}: {self.message[:30]}"
    
class RefreshTokenStoreManager(models.Manager):
    def prune_expired(self):                                            # 만료 토큰 일괄 삭제
        return self.filter(expires_at__lt=timezone.now()).delete()

    def replace_for_user(self, user, token, expires_at):                # 사용자 1개 정책: 있으면 갱신, 없으면 생성
        
        return self.update_or_create(
            user=user,
            defaults={
                "token": token,
                "expires_at": expires_at,
                "revoked": False,
            }
        )

class RefreshTokenStore(models.Model): # 어떤 유저의 토큰인지 연결 (1:N 관계)
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,  # 유저가 삭제되면 해당 토큰도 자동 삭제됨
        related_name="refresh_tokens"
    )

    token = models.CharField(max_length=512, unique=True) # 저장된 refresh token 문자열 (JWT 토큰 전체를 저장)
    created_at = models.DateTimeField(auto_now_add=True) # 토큰이 발급된 시각
    expires_at = models.DateTimeField() # 토큰이 만료되는 시각 (JWT의 exp 클레임과 동일하게 설정)
    revoked = models.BooleanField(default=False,) # 로그아웃 또는 강제 만료 처리된 경우 표시

    objects = RefreshTokenStoreManager()

    class Meta:
        # 최근에 발급된 순으로 정렬
        ordering = ['-created_at']
        verbose_name = "Refresh Token 저장소"
        verbose_name_plural = "Refresh Token 저장소 목록"

        constraints = [
            models.UniqueConstraint(fields=['user'], name='uq_refresh_one_per_user'),
        ]
        indexes = [
            models.Index(fields=['expires_at']), 
        ]

    def is_expired(self):
        
        return timezone.now() >= self.expires_at    # 현재 시간이 만료시간을 지난 경우 True 반환

    def __str__(self):
        return f"[{self.user.user_id}] refresh @ {self.created_at.strftime('%Y-%m-%d %H:%M:%S')}"