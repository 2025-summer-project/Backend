from django.urls import path
from .views import DocumentListView

urlpatterns = [
    path('document-list', DocumentListView.as_view()),          #get /doc/document-list
]