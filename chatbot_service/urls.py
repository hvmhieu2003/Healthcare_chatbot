from django.urls import path
from .views import Chatbot, chatbot_page, MedicalHistory

urlpatterns = [
    path('chat/', Chatbot.as_view(), name='chatbot'),
    path('history/', Chatbot.as_view(), name='chatbot_history'),
    path('medical-history/', MedicalHistory.as_view(), name='medical_history'),
    path('', chatbot_page, name='chatbot_page'),
]