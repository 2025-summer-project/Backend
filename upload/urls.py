from django.urls import path

from .import views

urlpatterns = [
    path('documents/', views.DocumentUploadView.as_view(), name='upload'),
]