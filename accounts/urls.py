from django.urls import path
from .views import SignupView, LoginView, LogoutView, LoginFormView, SignupFormView, LogoutFormView
from rest_framework_simplejwt.views import TokenRefreshView

# accounts 앱의 URL 경로 설정
urlpatterns = [
    path('signup', SignupView.as_view(), name='signup'),                            # POST /auth/signup
    path('login', LoginView.as_view(), name='login'),                               # POST /auth/login
    path('logout', LogoutView.as_view(), name='logout'),                            # POST /auth/refresh
    path('refresh', TokenRefreshView.as_view(), name='token_refresh'),              # POST /auth/refresh
    path('login-page', LoginFormView.as_view(), name='login-page'),    
    path("signup-page", SignupFormView.as_view(), name="signup_page"),
    path("logout-page", LogoutFormView.as_view(), name="logout_page"),
]
