from django.urls import path
from .views import PredictDisease

urlpatterns = [
    path('predict/', PredictDisease.as_view(), name='predict_disease'),
]