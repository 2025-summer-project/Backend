from django.urls import path

from .import views

urlpatterns = [
    path('chat/', views.ChatCreateView.as_view(), name='consult'),
]