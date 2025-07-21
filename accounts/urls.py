from django.urls import path
from .views import SignupView
from .views import CustomTokenObtainPairView
from rest_framework_simplejwt.views import TokenRefreshView

# accounts 앱의 URL 경로 설정
urlpatterns = [
    path('signup', SignupView.as_view(), name='signup'),                            # POST /auth/signup
    path('login', CustomTokenObtainPairView.as_view(), name='login'),               # POST /auth/login
    path('refresh', TokenRefreshView.as_view(), name='token_refresh'),              # POST /auth/refresh
]
