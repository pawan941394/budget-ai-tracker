from django.urls import path
from . import views

app_name = 'ai_chat_bot'

urlpatterns = [
    path('sessions/<str:username>/', views.chat_sessions, name='chat_sessions'),
    path('sessions/<str:username>/html/', views.chat_sessions_html, name='chat_sessions_html'),
    path('session/<str:session_id>/', views.chat_session_detail, name='chat_session_detail'),
    path('session/<str:session_id>/html/', views.chat_session_html, name='chat_session_html'),
]
