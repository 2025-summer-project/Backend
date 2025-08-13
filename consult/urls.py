from django.urls import path

from .import views

urlpatterns = [
    path('chat/', views.ChatCreateView.as_view(), name='consult'),
    path('<int:document_id>/chat/', views.ChatHistoryView.as_view(), name='chat-history'),
]