from django.urls import path
from .views import SignupView

# accounts 앱의 URL 경로 설정
urlpatterns = [
    path('signup', SignupView.as_view(), name='signup'),  # POST /auth/signup 으로 연결됨
]
