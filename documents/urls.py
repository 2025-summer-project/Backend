from django.urls import path
from .views import DocumentListView, UpdateFileNameView, ChatListView, UpdateChatNameView, DocumentPDFView,SummaryListView

urlpatterns = [
    path('document-list', DocumentListView.as_view()),          #get /doc/document-list
    path('chat-list', ChatListView.as_view()),                  #get /doc/chat-list
    path('documents/<int:pk>/document-name/', UpdateFileNameView.as_view(), name='document-name'),
    path('documents/<int:pk>/chat-name/', UpdateChatNameView.as_view(), name='chat-name'),
    path("<int:document_id>/pdf", DocumentPDFView.as_view(), name="document-pdf"),
    path('documents/summaries/', SummaryListView.as_view(), name='summary-list'),
]